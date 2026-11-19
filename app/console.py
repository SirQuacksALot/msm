import anyio
from docker.errors import NotFound

from . import docker_client


def _next_or_none(gen):
    try:
        return next(gen)
    except StopIteration:
        return None


async def stream_logs(container_name: str, tail: int = 200):
    """
    SSE-Generator: liest docker logs --follow und schickt jede Zeile
    als `data: <line>\\n\\n`-Event.
    """
    try:
        container = docker_client.get_client().containers.get(container_name)
    except NotFound:
        yield "event: error\ndata: container not found\n\n"
        return
    except Exception as e:
        yield f"event: error\ndata: {e}\n\n"
        return

    try:
        stream = container.logs(stream=True, follow=True, tail=tail)
    except Exception as e:
        yield f"event: error\ndata: {e}\n\n"
        return

    try:
        while True:
            try:
                line = await anyio.to_thread.run_sync(_next_or_none, stream)
            except Exception as e:
                yield f"event: error\ndata: {e}\n\n"
                break
            if line is None:
                break
            text = line.decode("utf-8", errors="replace").replace("\r", "")
            for single in text.split("\n"):
                yield f"data: {single}\n\n"
    finally:
        try:
            stream.close()
        except Exception:
            pass


def send_rcon(container_name: str, command: str) -> dict:
    """
    Führt `rcon-cli <command>` im itzg-Container aus.
    RCON_PASSWORD liest rcon-cli aus der Container-Env.
    """
    try:
        container = docker_client.get_container(container_name)
    except NotFound:
        return {"ok": False, "error": f"Container '{container_name}' nicht gefunden"}
    try:
        result = container.exec_run(["rcon-cli", command])
    except Exception as e:
        return {"ok": False, "error": str(e)}

    output = (result.output or b"").decode("utf-8", errors="replace")
    if result.exit_code != 0:
        return {"ok": False, "error": output or f"exit code {result.exit_code}"}
    return {"ok": True, "output": output}