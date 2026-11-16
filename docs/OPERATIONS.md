# Operations — Raspberry Pi 5

## Assumptions
Raspberry Pi 5 ARM64 Linux, Docker Engine/Compose and Tailscale are already installed. This project must not reinstall them or modify existing Hermes, FreeLLMAPI, Open WebUI, SilverBullet or other containers.

## Deploy
1. Clone the repository and enter its root.
2. Run bash scripts/deploy-pi.sh. On first run it creates .env with two distinct random credentials, restricts file permissions, validates Compose, builds and starts the service, and checks health.
3. Inspect docker compose ps and docker compose logs -f orchestra.
4. Keep .env private and back up the credentials securely. The script does not modify Tailscale or any other containers.

The Docker image is based on python:3.12-slim and should support ARM64; the actual Pi build must be observed before calling it validated.

## Remote access
Docker binds 127.0.0.1:8788 on the Pi by default. This avoids LAN/public exposure. For direct IP-only access over Tailscale, run tailscale ip -4 on the Pi and set ORCHESTRA_BIND_ADDRESS in .env to that exact Tailscale interface IP; do not use 0.0.0.0. Recreate the container after changing the bind address. Alternatively, keep loopback binding and use Tailscale Serve as a private HTTPS proxy. Inspect existing Serve mappings before adding one; never overwrite another service's route. Do not expose the admin API to the public Internet.

## Updates
Back up the database first. Pull the intended branch, rebuild and restart. Keep the previous image and backup available for rollback. Never use docker compose down -v; that removes the persistent volume.

## Backup
Use SQLite's online backup API or a consistent volume snapshot. Do not copy only the main database file while WAL writes are active. Rehearse restore on a separate test instance.

## Monitoring
Inspect compose ps/logs, /health, docker stats, df -h, worker heartbeat age, queue age, failed tasks and lease expirations. Keep the database volume on reliable storage with free space.
