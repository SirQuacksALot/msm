import os
import re
from pathlib import Path
import yaml

INSTANCES_DIR = Path(os.environ.get("INSTANCES_DIR", "instances"))

def sanitize_id(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name).strip("-")
    return s or "server"

def instance_path(iid: str) -> Path:
    return INSTANCES_DIR / f"{iid}.yaml"

def load_instance(iid: str):
    p = instance_path(iid)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_instance(iid: str, data: dict):
    INSTANCES_DIR.mkdir(parents=True, exist_ok=True)
    with open(instance_path(iid), "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def _apply_defaults(fields: dict, target: dict):
    for key, spec in (fields or {}).items():
        if not isinstance(spec, dict):
            continue
        # leaf, wenn "type" oder "default" direkt drin ist
        if "type" in spec or "default" in spec:
            if key not in target and "default" in spec:
                target[key] = spec["default"]
        else:
            sub = target.setdefault(key, {})
            _apply_defaults(spec, sub)

def render_defaults(template: dict) -> dict:
    data = {"managed": {}, "server": {}}
    _apply_defaults(template.get("fields") or {}, data)
    return data

def ensure_instance(container, template: dict):
    labels = container.labels or {}
    iid = labels.get("mc-manager.instance") or sanitize_id(container.name)
    existing = load_instance(iid)
    if existing is not None:
        return iid, existing, False
    data = {
        "id": iid,
        "container_name": container.name,
        "template": template.get("id", "generic"),
        "display_name": container.name,
    }
    defaults = render_defaults(template)
    data["managed"] = defaults["managed"]
    data["server"] = defaults["server"]
    save_instance(iid, data)
    return iid, data, True

def list_instance_files():
    if not INSTANCES_DIR.exists():
        return []
    return sorted(INSTANCES_DIR.glob("*.yaml"))

SPEC_KEYS = {"type", "default", "editable", "values"}
