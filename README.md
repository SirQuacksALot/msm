<img src="./assets/icon.svg" width="150" alt="Icon" align="left">

### MSM ( MC Stack Manager )

is a web-based management interface for Minecraft servers running within a Docker Compose stack. It provides a centralized and intuitive way to manage and monitor all Minecraft server instances and their services.

> [!WARNING] Warning - No Authentication
>
> This project does not include built-in authentication. It is designed to run behind a reverse proxy with a properly configured authentication layer. A simple proxy-level authentication mechanism is sufficient if it meets your security requirements.

<br>

<img src="./assets/preview-left.png" alt="Preview left" align="left"> <img src="./assets/preview-right.png" alt="Preview right" align="right">

<br>

## How it works

> Not done yet...

## Templates

> Not done yet...

## Deployment

1. Create `docker-compose.yaml`

```yaml
---
services:
  manager:
    image: SirQuacksALot/msm:latest
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./instances:/app/instances
      - ./backups:/app/backups
    environment:
      - STACK_PROJECT=${COMPOSE_PROJECT_NAME}
    labels:
      - "mc-manager.enable=true"

  mc-survival:
    image: itzg/minecraft-server:latest
    labels:
      - "mc-manager.enable=true"
      - "mc-manager.template=paper"
    environment:
      EULA: "TRUE"
      TYPE: "PAPER"
      ENABLE_RCON: "true"
      RCON_PASSWORD: "secret"
    ports:
      - "127.0.0.1:25566:25565"
```

2. Run the following

```bash
docker compose up -d
```

3. Access UI at http://127.0.0.1:8080


> [!NOTE] Note - Localhost & Reverse Proxy
>
>
> The provided example is configured for localhost access only. If you need access beyond localhost, make sure to configure a reverse proxy with an authentication layer of your choice.
>
> Without proper authentication, anyone who can access the application may also gain access to the Minecraft servers managed by it, potentially allowing unauthorized control or misuse.


---

**Todo list:**

- Kleine liste der erkannten servers mit "name", "öffnen" button und "files" button als nav bar 

