from dataclasses import dataclass
import json
import os
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    admin_token: str
    worker_token: str
    database: Path
    lease_seconds: int
    max_runtime_seconds: int
    log_level: str

    @classmethod
    def from_env(cls):
        admin = os.getenv("ORCHESTRA_ADMIN_TOKEN", "")
        worker = os.getenv("ORCHESTRA_WORKER_TOKEN", "")
        if len(admin) < 32 or len(worker) < 32 or admin == worker:
            raise RuntimeError("Set two different tokens, each at least 32 characters.")
        return cls(admin, worker, Path(os.getenv("ORCHESTRA_DATABASE", "/data/orchestra.sqlite3")),
                   max(30, int(os.getenv("ORCHESTRA_TASK_LEASE_SECONDS", "180"))),
                   max(60, int(os.getenv("ORCHESTRA_MAX_TASK_RUNTIME_SECONDS", "3600"))),
                   os.getenv("ORCHESTRA_LOG_LEVEL", "INFO").upper())

def executor_map():
    value = json.loads(os.getenv("ORCHESTRA_EXECUTORS", "{}"))
    if not isinstance(value, dict):
        raise RuntimeError("ORCHESTRA_EXECUTORS must be a JSON object")
    for name, argv in value.items():
        if not isinstance(name, str) or not name or not isinstance(argv, list) or not argv:
            raise RuntimeError("Each executor must map a name to a non-empty argv array")
        if not all(isinstance(arg, str) and arg for arg in argv):
            raise RuntimeError("Executor argv entries must be non-empty strings")
    return value
