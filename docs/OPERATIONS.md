# Operations — Raspberry Pi 5

## Assumptions
Raspberry Pi 5 ARM64 Linux, Docker Engine/Compose and Tailscale are already installed. This project must not reinstall them or modify existing Hermes, FreeLLMAPI, Open WebUI, SilverBullet or other containers.

## Deploy
1. Clone the repository and enter its root.
2. Copy .env.example to .env; chmod 600 .env.
3. Generate two different values with openssl rand -hex 32 and set admin and worker tokens.
4. Run docker compose up -d --build.
5. Inspect docker compose ps and docker compose logs -f orchestra.
6. Check curl -fsS http://127.0.0.1:8788/health.

The Docker image is based on python:3.12-slim and should support ARM64; the actual Pi build must be observed before calling it validated.

## Remote access
Docker binds 127.0.0.1:8788 on the Pi by default. This avoids LAN/public exposure. For direct IP-only access over Tailscale, run tailscale ip -4 on the Pi and set ORCHESTRA_BIND_ADDRESS in .env to that exact Tailscale interface IP; do not use 0.0.0.0. Recreate the container after changing the bind address. Alternatively, keep loopback binding and use Tailscale Serve as a private HTTPS proxy. Inspect existing Serve mappings before adding one; never overwrite another service's route. Do not expose the admin API to the public Internet.

## Updates
Back up the database first. Pull the intended branch, rebuild and restart. Keep the previous image and backup available for rollback. Never use docker compose down -v; that removes the persistent volume.

## Backup
Use SQLite's online backup API or a consistent volume snapshot. Do not copy only the main database file while WAL writes are active. Rehearse restore on a separate test instance.

## Monitoring
Inspect compose ps/logs, /health, docker stats, df -h, worker heartbeat age, queue age, failed tasks and lease expirations. Keep the database volume on reliable storage with free space.
