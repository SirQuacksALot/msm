import os
import time
import docker

_client = None

# Discovery-Cache (5 s TTL), damit die Übersicht nicht bei jedem Request `docker ps` macht
_cache = {"ts": 0.0, "data": None}
CACHE_TTL = 5.0


def get_client():
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def get_own_container():
    hostname = os.environ.get("HOSTNAME", "")
    if not hostname:
        return None
    try:
        return get_client().containers.get(hostname)
    except Exception:
        return None


def get_stack_project():
    for key in ("STACK_PROJECT", "COMPOSE_PROJECT_NAME"):
        val = os.environ.get(key)
        if val:
            return val
    own = get_own_container()
    if own:
        return (own.labels or {}).get("com.docker.compose.project")
    return None


def list_stack_containers(project):
    filters = {"label": [f"com.docker.compose.project={project}"]} if project else {}
    return get_client().containers.list(all=True, filters=filters)


def env_dict(container):
    env = container.attrs.get("Config", {}).get("Env", []) or []
    d = {}
    for item in env:
        if "=" in item:
            k, v = item.split("=", 1)
            d[k] = v
    return d


def image_ref(container):
    if container.image.tags:
        return container.image.tags[0]
    return container.attrs.get("Config", {}).get("Image", "")


def is_minecraft_container(container):
    if (container.labels or {}).get("mc-manager.enable") == "true":
        return True
    if "EULA" in env_dict(container):
        return True
    if "itzg/minecraft" in image_ref(container):
        return True
    return False


# ---- Lifecycle --------------------------------------------------------------

def get_container(name):
    return get_client().containers.get(name)


def start_container(name):
    return get_container(name).start()


def stop_container(name, timeout=30):
    return get_container(name).stop(timeout=timeout)


def restart_container(name, timeout=30):
    return get_container(name).restart(timeout=timeout)


def container_state(name):
    try:
        c = get_container(name)
    except Exception:
        return {"status": "missing", "health": None}
    state = c.attrs.get("State", {}) or {}
    return {
        "status": c.status,
        "health": (state.get("Health") or {}).get("Status"),
    }


# ---- Discovery-Cache --------------------------------------------------------

def cache_get():
    if _cache["data"] is not None and (time.time() - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]
    return None


def cache_set(data):
    _cache["ts"] = time.time()
    _cache["data"] = data


def cache_invalidate():
    _cache["ts"] = 0.0
    _cache["data"] = None