# Deploy

## Local full stack

Requirements:

- Docker Desktop with WSL 2 backend;
- the `data/runtime` directory with the database, maps and previews.

Start backend and nginx:

```powershell
cd deploy
docker compose up --build -d
```

Open http://localhost:8080.

By default:

- nginx listens on host port `8080`;
- backend listens inside the Compose network on `8652`;
- the frontend is built inside the nginx image and uses relative API URLs,
  so the same image works on `localhost`, a LAN IP and a public domain;
- backend runs with **2 Uvicorn workers**.

Run Compose from this directory. `docker compose` reads `deploy/.env` only
when the working directory contains it.

Stop:

```powershell
cd deploy
docker compose down
```

Logs:

```powershell
cd deploy
docker compose logs -f backend
docker compose logs -f nginx
```

## Configuration

Copy `.env.example` to `.env` in this directory if you need to change values:

```text
VITE_API_URL=
BACKEND_UPSTREAM=backend:8652
WEB_BIND=0.0.0.0
WEB_PORT=8080
HOST_RUNTIME_DIR=../data/runtime
HOST_LOG_DIR=../logs
WEB_CONCURRENCY=2
REDROOM_LOG_LEVEL=INFO
```

- `VITE_API_URL` is embedded at build time. Leave it empty when the frontend
  and API share one origin (recommended). Set an absolute URL only for a
  split deployment and rebuild the nginx image afterwards.
- `BACKEND_UPSTREAM` is the FastAPI address **without** `http://`, as seen
  from the nginx container. With the full stack it is `backend:8652`.
- `WEB_BIND` and `WEB_PORT` control the published nginx socket. Use
  `WEB_BIND=127.0.0.1` when a host reverse proxy terminates TLS.
- `HOST_RUNTIME_DIR` and `HOST_LOG_DIR` are host paths mounted into the
  backend. Relative paths are resolved from this directory.
- `WEB_CONCURRENCY` controls the number of Uvicorn worker processes.
- `REDROOM_CORS_ORIGINS` (comma-separated) is needed only when the frontend
  and API are served from different origins.

## Data and logs

The backend mounts:

```text
data/runtime  → /data/runtime
logs/         → /logs
```

The database, maps and previews are read from `data/runtime`. The application
does not need `data/work`, `data/releases` or `data/backups`.

The map version is computed once per backend worker at startup. After changing
files in `data/runtime/maps`, restart the backend so browsers receive the new
map version. On Docker Desktop for Windows this startup scan can take a few
seconds because the data directory is a bind mount; requests after startup are
fast.

## Production

Server layout:

```text
/srv/redroom/
  data/
    releases/2026-11-20/
    current -> releases/2026-11-20
  logs/
  app/            # this repository
```

`deploy/.env`:

```text
VITE_API_URL=
BACKEND_UPSTREAM=backend:8652
WEB_BIND=127.0.0.1
WEB_PORT=8080
HOST_RUNTIME_DIR=/srv/redroom/data/current
HOST_LOG_DIR=/srv/redroom/logs
WEB_CONCURRENCY=2
REDROOM_LOG_LEVEL=INFO
```

```bash
cd deploy
docker compose up --build -d
python ../scripts/smoke_test.py --base-url http://127.0.0.1:8080
```

`WEB_BIND=127.0.0.1` assumes TLS is terminated by a host reverse proxy.
If the container nginx serves port 80 directly, use `WEB_BIND=0.0.0.0` and
`WEB_PORT=80`.

TLS is usually terminated by a host reverse proxy (Caddy, host nginx with
certbot) that proxies to the published nginx port.

### Updates

- Code or frontend: `git pull && docker compose up --build -d`.
- Data: switch the `current` symlink and recreate the backend:
  `docker compose up -d --force-recreate backend && docker compose restart nginx`.
  A plain `restart` can keep the old bind mount.
- Database only: no restart is needed; the DB version is derived from
  `mtime`.
- History groups (`backend/app/data/history_groups.json`) are part of the
  image: rebuild the backend after changing them.
- After `docker compose up -d backend` run `docker compose restart nginx`.
  Nginx resolves the backend host once at startup and can return 502 after
  the container is recreated with another IP.
