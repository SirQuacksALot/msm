import io
import posixpath
import tarfile
import time
from datetime import datetime, timezone
from pathlib import PurePosixPath

from docker.errors import APIError, NotFound

from . import docker_client

COMMON_ROOTS = ("/data", "/server", "/config")
_root_cache: dict[str, str] = {}


# ---- Container / Root-Detection ---------------------------------------------

def _container(container_name: str):
    try:
        return docker_client.get_container(container_name)
    except NotFound:
        raise ValueError(f"Container '{container_name}' nicht gefunden")


def _detect_root(c) -> str:
    # 1) Label-Override (z.B. mc-manager.data-root=/server)
    label = (c.labels or {}).get("mc-manager.data-root")
    if label:
        return label

    # 2) Bekannte Pfade im laufenden Container testen
    if c.status == "running":
        for path in COMMON_ROOTS:
            try:
                if c.exec_run(["test", "-d", path]).exit_code == 0:
                    return path
            except APIError:
                continue

    # 3) Aus den Mounts ableiten (erstes Single-Level-Ziel)
    for m in c.attrs.get("Mounts", []):
        dest = m.get("Destination")
        if dest and dest != "/" and dest.count("/") == 1:
            return dest

    return "/data"


def data_root(container_name: str) -> str:
    if container_name not in _root_cache:
        _root_cache[container_name] = _detect_root(_container(container_name))
    return _root_cache[container_name]


def invalidate_cache(container_name: str | None = None):
    if container_name is None:
        _root_cache.clear()
    else:
        _root_cache.pop(container_name, None)


def _check_running(c):
    if c.status != "running":
        raise ValueError(
            f"Container '{c.name}' läuft nicht – Dateizugriff nur bei laufendem Server"
        )


def _safe_join(root: str, rel: str) -> str:
    rel = (rel or "").lstrip("/")
    norm = posixpath.normpath(posixpath.join(root, rel))
    if not (norm == root or norm.startswith(root + "/")):
        raise ValueError(f"Pfad außerhalb von {root}: {rel}")
    return norm


# ---- Verzeichnis listen -----------------------------------------------------

def list_dir(container_name: str, rel: str) -> dict:
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target = _safe_join(root, rel)

    if c.exec_run(["test", "-d", target]).exit_code != 0:
        raise ValueError(f"Verzeichnis existiert nicht: {rel or '/'}")

    # busybox-taugliches Auflisten (kein GNU-find -printf)
    script = (
        'cd "$1" || exit 1; '
        'for f in * .[!.]*; do '
        '[ -e "$f" ] || continue; '
        'stat -c "%F|%s|%Y|%n" "$f" 2>/dev/null; '
        'done'
    )
    res = c.exec_run(["sh", "-c", script, "sh", target])
    if res.exit_code != 0:
        err = res.output.decode("utf-8", "replace").strip()
        raise ValueError(err or "Auflisten fehlgeschlagen")

    entries = []
    for line in res.output.decode("utf-8", "replace").splitlines():
        if not line.strip() or "|" not in line:
            continue
        ftype, size, epoch, name = line.split("|", 3)
        is_dir = "directory" in ftype.lower()
        is_file = "regular" in ftype.lower()
        try:
            mtime = datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
        except (ValueError, OverflowError):
            mtime = datetime.now(timezone.utc).isoformat()
        entries.append({
            "name": name,
            "type": "dir" if is_dir else "file",
            "size": int(size) if is_file else None,
            "mtime": mtime,
            "rel": posixpath.relpath(posixpath.join(target, name), root),
        })

    entries.sort(key=lambda e: (e["type"] != "dir", e["name"].lower()))

    if target == root:
        current, parent = "", ""
    else:
        current = posixpath.relpath(target, root)
        parent = posixpath.relpath(posixpath.dirname(target), root)
        if parent == ".":
            parent = ""

    return {"path": current, "parent": parent, "entries": entries}


# ---- Lesen / Schreiben ------------------------------------------------------

def read_text(container_name: str, rel: str, max_bytes: int = 1024 * 1024) -> dict:
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target = _safe_join(root, rel)

    stat = c.exec_run(["stat", "-c", "%s", target])
    if stat.exit_code != 0:
        raise ValueError("Datei nicht gefunden")
    size = int(stat.output.decode().strip())
    if size > max_bytes:
        return {"too_large": True, "size": size}

    res = c.exec_run(["cat", target])
    if res.exit_code != 0:
        raise ValueError(res.output.decode("utf-8", "replace").strip() or "Lesen fehlgeschlagen")
    try:
        return {"content": res.output.decode("utf-8")}
    except UnicodeDecodeError:
        return {"binary": True, "size": size}


def write_text(container_name: str, rel: str, content: str):
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target = _safe_join(root, rel)
    parent = posixpath.dirname(target)
    name = posixpath.basename(target)

    c.exec_run(["mkdir", "-p", parent])

    buf = io.BytesIO()
    data = content.encode("utf-8")
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=name)
        info.size = len(data)
        info.mtime = int(time.time())
        tar.addfile(info, io.BytesIO(data))
    buf.seek(0)

    if not c.put_archive(parent, buf):
        raise ValueError("Schreiben fehlgeschlagen")


def get_download_stream(container_name: str, rel: str) -> tuple[bytes, str]:
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target = _safe_join(root, rel)

    try:
        stream, _ = c.get_archive(target)
    except NotFound:
        raise ValueError("Datei nicht gefunden")

    buf = io.BytesIO(b"".join(stream))
    with tarfile.open(fileobj=buf, mode="r") as tar:
        member = next((m for m in tar.getmembers() if m.isfile()), None)
        if not member:
            raise ValueError("keine reguläre Datei")
        data = tar.extractfile(member).read()

    return data, posixpath.basename(target)


# ---- Mutationen -------------------------------------------------------------

def delete(container_name: str, rel: str):
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target = _safe_join(root, rel)
    if target == root:
        raise ValueError("Root kann nicht gelöscht werden")
    res = c.exec_run(["rm", "-rf", target])
    if res.exit_code != 0:
        raise ValueError(res.output.decode("utf-8", "replace").strip() or "Löschen fehlgeschlagen")


def mkdir(container_name: str, rel: str):
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target = _safe_join(root, rel)
    res = c.exec_run(["mkdir", "-p", target])
    if res.exit_code != 0:
        raise ValueError(res.output.decode("utf-8", "replace").strip() or "Ordner erstellen fehlgeschlagen")


def copy_or_move(container_name: str, src: str, dst: str, move: bool = False):
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    src_p = _safe_join(root, src)
    dst_p = _safe_join(root, dst)
    if src_p == root:
        raise ValueError("Root kann nicht kopiert werden")
    res = c.exec_run([("mv" if move else "cp"), "-a", src_p, dst_p])
    if res.exit_code != 0:
        raise ValueError(res.output.decode("utf-8", "replace").strip() or "Kopieren/Verschieben fehlgeschlagen")


def save_upload(container_name: str, rel_dir: str, filename: str, data: bytes):
    c = _container(container_name)
    _check_running(c)
    root = data_root(container_name)
    target_dir = _safe_join(root, rel_dir)
    safe_name = PurePosixPath(filename).name
    if not safe_name or safe_name in (".", ".."):
        raise ValueError("ungültiger Dateiname")

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=safe_name)
        info.size = len(data)
        info.mtime = int(time.time())
        tar.addfile(info, io.BytesIO(data))
    buf.seek(0)

    if not c.put_archive(target_dir, buf):
        raise ValueError("Upload fehlgeschlagen")