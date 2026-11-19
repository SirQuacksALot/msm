import os
from pathlib import Path

from fastapi.responses import FileResponse, Response, StreamingResponse
import anyio
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from docker.errors import APIError, NotFound

from . import console, docker_client, templates_loader, files_docker as fops
from . import instances as inst

DIST = Path("web/dist")
app = FastAPI(title="MC Stack Manager")

# Gebaute Vite-Assets (nur wenn Build vorhanden)
if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")


# ---- Discovery --------------------------------------------------------------

def _build_discovery():
    project = docker_client.get_stack_project()
    containers = docker_client.list_stack_containers(project)
    templates_loader.load_templates()
    own = docker_client.get_own_container()
    own_id = own.id if own else None

    result = []
    for c in containers:
        if c.id == own_id:
            continue
        if not docker_client.is_minecraft_container(c):
            continue
        env = docker_client.env_dict(c)
        image = docker_client.image_ref(c)
        tpl = templates_loader.match_template(c, env, image)
        iid, data, created = inst.ensure_instance(c, tpl)
        state = c.attrs.get("State", {}) or {}
        health = (state.get("Health") or {}).get("Status")
        result.append({
            "id": iid,
            "container_name": c.name,
            "display_name": data.get("display_name", c.name),
            "template": data.get("template"),
            "status": c.status,
            "health": health,
            "created": created,
            "container_id": c.short_id,
        })
    result.sort(key=lambda s: s["id"])
    return result


def discover(force: bool = False):
    if force:
        docker_client.cache_invalidate()
    cached = docker_client.cache_get()
    if cached is not None:
        return cached
    data = _build_discovery()
    docker_client.cache_set(data)
    return data


def _load_instance_or_404(sid: str):
    instance = inst.load_instance(sid)
    if not instance:
        raise HTTPException(404, f"Instanz '{sid}' nicht gefunden")
    return instance


def _container_name(instance: dict) -> str:
    name = instance.get("container_name") or instance.get("id")
    if not name:
        raise HTTPException(500, "Instanz hat weder container_name noch id")
    return str(name)


# ---- API: Servers -----------------------------------------------------------

@app.get("/api/servers")
def api_servers(refresh: int = 0):
    return discover(force=bool(refresh))


@app.get("/api/servers/{sid}")
def api_server(sid: str):
    instance = _load_instance_or_404(sid)
    name = _container_name(instance)
    st = docker_client.container_state(name)
    return {
        "id": sid,
        "instance": instance,
        "status": st["status"],
        "health": st["health"],
    }


def _lifecycle(sid: str, fn, label: str):
    instance = _load_instance_or_404(sid)
    name = _container_name(instance)
    try:
        fn(name)
    except NotFound:
        raise HTTPException(404, f"Container '{name}' nicht gefunden")
    except APIError as e:
        raise HTTPException(500, f"{label} fehlgeschlagen: {str(e).splitlines()[0]}")
    docker_client.cache_invalidate()
    return {"ok": True, "action": label.lower()}


@app.post("/api/servers/{sid}/start")
def api_start(sid: str):
    return _lifecycle(sid, docker_client.start_container, "Start")


@app.post("/api/servers/{sid}/stop")
def api_stop(sid: str):
    return _lifecycle(sid, docker_client.stop_container, "Stop")


@app.post("/api/servers/{sid}/restart")
def api_restart(sid: str):
    return _lifecycle(sid, docker_client.restart_container, "Restart")


# ---- API: Console -----------------------------------------------------------

@app.get("/api/servers/{sid}/console/stream")
async def api_stream(sid: str):
    instance = _load_instance_or_404(sid)
    name = _container_name(instance)
    return StreamingResponse(
        console.stream_logs(name),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/servers/{sid}/console/command")
async def api_command(sid: str, request: Request):
    instance = _load_instance_or_404(sid)
    body = await request.json()
    cmd = (body.get("command") or "").strip()
    if not cmd:
        raise HTTPException(400, "leeres Kommando")
    name = _container_name(instance)
    result = await anyio.to_thread.run_sync(console.send_rcon, name, cmd)
    return result


# ---- API: Dateimanager ------------------------------------------------------

@app.get("/api/servers/{sid}/files")
def api_files(sid: str, path: str = ""):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    try:
        return fops.list_dir(cname, path)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/servers/{sid}/files/download")
def api_files_download(sid: str, path: str):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    try:
        data, filename = fops.get_download_stream(cname, path)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/servers/{sid}/files/read")
def api_files_read(sid: str, path: str):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    try:
        return fops.read_text(cname, path)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/servers/{sid}/files/write")
async def api_files_write(sid: str, request: Request):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    body = await request.json()
    try:
        fops.write_text(cname, body.get("path", ""), body.get("content", ""))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/servers/{sid}/files/delete")
async def api_files_delete(sid: str, request: Request):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    body = await request.json()
    try:
        fops.delete(cname, body.get("path", ""))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/servers/{sid}/files/mkdir")
async def api_files_mkdir(sid: str, request: Request):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    body = await request.json()
    parent = body.get("parent", "")
    name = (body.get("name") or "").strip()
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise HTTPException(400, "ungültiger Name")
    new_path = f"{parent}/{name}".lstrip("/") if parent else name
    try:
        fops.mkdir(cname, new_path)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/servers/{sid}/files/copy")
async def api_files_copy(sid: str, request: Request):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    body = await request.json()
    try:
        fops.copy_or_move(
            cname, body.get("src", ""), body.get("dst", ""), move=bool(body.get("move"))
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/servers/{sid}/files/upload")
async def api_files_upload(sid: str, request: Request, path: str = ""):
    instance = _load_instance_or_404(sid)
    cname = _container_name(instance)
    form = await request.form()
    upload = form.get("file")
    if not upload or not hasattr(upload, "read"):
        raise HTTPException(400, "keine Datei")
    data = await upload.read()
    try:
        fops.save_upload(cname, path, upload.filename or "upload.bin", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}

# ---- Health & SPA-Fallback (müssen zuletzt stehen) --------------------------

@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/{full_path:path}", include_in_schema=False)
async def spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404)
    idx = DIST / "index.html"
    if not idx.exists():
        raise HTTPException(503, "Frontend nicht gebaut (web/dist/index.html fehlt)")
    return FileResponse(str(idx))