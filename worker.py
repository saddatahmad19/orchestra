from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx

from orchestra.config import executor_map

BASE_URL = os.getenv("ORCHESTRA_SERVER_URL", "http://127.0.0.1:8788").rstrip("/")
TOKEN = os.getenv("ORCHESTRA_WORKER_TOKEN", "")
WORKER_ID = os.getenv("ORCHESTRA_WORKER_ID", socket.gethostname() + "-" + str(uuid.getnode()))
WORKER_NAME = os.getenv("ORCHESTRA_WORKER_NAME", socket.gethostname())
POLL_SECONDS = max(2, int(os.getenv("ORCHESTRA_WORKER_POLL_SECONDS", "4")))
HEARTBEAT_SECONDS = max(10, int(os.getenv("ORCHESTRA_WORKER_HEARTBEAT_SECONDS", "30")))
PROJECT_ROOTS = [Path(p).expanduser().resolve() for p in os.getenv("ORCHESTRA_PROJECT_ROOTS", "").split(os.pathsep) if p]
MAX_RUNTIME = max(60, int(os.getenv("ORCHESTRA_WORKER_MAX_RUNTIME_SECONDS", "3600")))
MAX_OUTPUT = 90_000

def headers():
    if len(TOKEN) < 32:
        raise RuntimeError("ORCHESTRA_WORKER_TOKEN must contain at least 32 characters")
    return {"Authorization": "Bearer " + TOKEN}

def api(client, method, path, **kwargs):
    response = client.request(method, BASE_URL + path, headers=headers(), timeout=20, **kwargs)
    response.raise_for_status()
    return response.json()

def project_directory(raw: str | None) -> Path:
    if not raw:
        raise RuntimeError("Task has no project_path; worker policy requires an explicit project")
    candidate = Path(raw).expanduser().resolve(strict=True)
    if not candidate.is_dir():
        raise RuntimeError("Project path is not a directory")
    if not PROJECT_ROOTS or not any(candidate == root or candidate.is_relative_to(root) for root in PROJECT_ROOTS):
        raise RuntimeError("Project path is outside ORCHESTRA_PROJECT_ROOTS")
    return candidate

def output_tail(file_obj, limit=MAX_OUTPUT // 2) -> str:
    file_obj.flush()
    size = file_obj.tell()
    file_obj.seek(max(0, size - limit))
    return file_obj.read(limit).decode("utf-8", errors="replace")

def run_task(client: httpx.Client, task: dict, executors: dict):
    task_id = task["id"]
    try:
        cwd = project_directory(task.get("project_path"))
        argv_template = executors.get(task["engine"])
        if not argv_template:
            raise RuntimeError("No verified argv configuration for executor: " + task["engine"])
        has_prompt_arg = any("{prompt}" in part for part in argv_template)
        argv = [part.replace("{project_path}", str(cwd)).replace("{prompt}", task["prompt"])
                for part in argv_template]
        if not all(isinstance(part, str) and part for part in argv):
            raise RuntimeError("Invalid executor argv")
        safe_env_keys = {"PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL",
                         "XDG_CONFIG_HOME", "XDG_DATA_HOME", "TERM"}
        safe_env_keys.update(k for k in os.getenv("ORCHESTRA_WORKER_ENV_ALLOWLIST", "").split(",") if k)
        env = {k: v for k, v in os.environ.items() if k in safe_env_keys}
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            proc = subprocess.Popen(
                argv, cwd=str(cwd), env=env, shell=False,
                stdin=subprocess.PIPE if not has_prompt_arg else subprocess.DEVNULL,
                stdout=stdout_file, stderr=stderr_file, close_fds=True,
            )
            if not has_prompt_arg:
                proc.stdin.write(task["prompt"].encode("utf-8"))
                proc.stdin.close()
            started = time.monotonic()
            next_renew = started + 45
            next_state = started + 8
            cancelled = False
            while proc.poll() is None:
                now = time.monotonic()
                if now - started > MAX_RUNTIME:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    raise TimeoutError("Executor exceeded worker runtime limit")
                try:
                    if now >= next_renew:
                        api(client, "POST", "/api/v1/workers/renew",
                            params={"task_id": task_id, "worker_id": WORKER_ID})
                        next_renew = now + 45
                    if now >= next_state:
                        state = api(client, "GET", f"/api/v1/workers/tasks/{task_id}/state",
                                    params={"worker_id": WORKER_ID})
                        if state["status"] == "cancelled":
                            cancelled = True
                            proc.terminate()
                            try:
                                proc.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                proc.kill()
                            break
                        next_state = now + 8
                except Exception as control_error:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    raise RuntimeError("Control plane became unavailable; executor was stopped") from control_error
                time.sleep(1)
            return_code = proc.wait()
            result = "stdout:\n" + output_tail(stdout_file) + "\nstderr:\n" + output_tail(stderr_file)
            if cancelled:
                return
            status = "succeeded" if return_code == 0 else "failed"
            api(client, "POST", f"/api/v1/tasks/{task_id}/complete",
                json={"worker_id": WORKER_ID, "status": status,
                      "result": result if status == "succeeded" else None,
                      "error": result[-18000:] if status == "failed" else None})
    except Exception as exc:
        try:
            api(client, "POST", f"/api/v1/tasks/{task_id}/complete",
                json={"worker_id": WORKER_ID, "status": "failed", "error": str(exc)[:20000]})
        except Exception:
            print("Task failure could not be reported; task lease will expire.")

def main():
    if not TOKEN:
        raise SystemExit("Set ORCHESTRA_WORKER_TOKEN")
    executors = executor_map()
    capabilities = sorted(executors)
    print("Orchestra worker starting:", WORKER_ID, "executors:", ", ".join(capabilities) or "none")
    last_heartbeat = 0.0
    with httpx.Client(trust_env=False) as client:
        while True:
            now = time.monotonic()
            if now - last_heartbeat >= HEARTBEAT_SECONDS:
                api(client, "POST", "/api/v1/workers/heartbeat", json={
                    "worker_id": WORKER_ID, "name": WORKER_NAME,
                    "hostname": socket.gethostname(), "platform": platform.platform(),
                    "capabilities": capabilities,
                })
                last_heartbeat = now
            claimed = api(client, "POST", "/api/v1/workers/claim",
                          params={"worker_id": WORKER_ID}).get("task")
            if not claimed:
                time.sleep(POLL_SECONDS)
                continue
            print("Claimed task:", claimed["id"], claimed["title"])
            run_task(client, claimed, executors)

if __name__ == "__main__":
    main()
