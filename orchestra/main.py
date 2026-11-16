from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import require_token
from .config import Settings
from .db import Database
from .schemas import TaskCompletion, TaskCreate, WorkerHeartbeat

settings = Settings.from_env()
db = Database(settings.database)
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("orchestra")

def admin(authorization: str | None):
    require_token(authorization, settings.admin_token)

def worker(authorization: str | None):
    require_token(authorization, settings.worker_token)

def add_event(conn, kind, message, task_id=None, worker_id=None):
    conn.execute(
        "INSERT INTO events(task_id,worker_id,kind,message,created_at) VALUES(?,?,?,?,?)",
        (task_id, worker_id, kind, str(message)[:2000], time.time()),
    )

def serialize_task(row):
    result = dict(row)
    result["approval_required"] = bool(result["approval_required"])
    return result

@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("Orchestra control plane started; database=%s", settings.database)
    yield
    log.info("Orchestra control plane stopped")

app = FastAPI(title="Orchestra", version="0.1.0", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory="web"), name="assets")

@app.get("/")
def index():
    return FileResponse("web/index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestra-control-plane", "time": time.time()}

@app.get("/api/v1/overview")
def overview(authorization: str | None = Header(default=None)):
    admin(authorization)
    with db.connect() as conn:
        counts = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status,COUNT(*) n FROM tasks GROUP BY status")}
        workers = [dict(r) for r in conn.execute(
            "SELECT id,name,hostname,platform,capabilities,last_seen,"
            "CASE WHEN last_seen > ? THEN 'online' ELSE 'offline' END AS status "
            "FROM workers ORDER BY name", (time.time() - 90,))]
        events = [dict(r) for r in conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT 30")]
    return {"task_counts": counts, "workers": workers, "recent_events": events}

@app.post("/api/v1/tasks", status_code=201)
def create_task(body: TaskCreate, authorization: str | None = Header(default=None)):
    admin(authorization)
    now, task_id = time.time(), str(uuid.uuid4())
    status = "pending_approval" if body.approval_required else "queued"
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO tasks(id,title,prompt,engine,project_path,status,approval_required,
            max_attempts,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (task_id, body.title, body.prompt, body.engine, body.project_path, status,
             int(body.approval_required), body.max_attempts, now, now))
        add_event(conn, "task.created", "Task created: " + status, task_id)
    return {"id": task_id, "status": status}

@app.get("/api/v1/tasks")
def list_tasks(status: str | None = None, limit: int = 50,
               authorization: str | None = Header(default=None)):
    admin(authorization)
    limit = min(max(limit, 1), 200)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE (? IS NULL OR status=?) ORDER BY created_at DESC LIMIT ?",
            (status, status, limit))
        return [serialize_task(r) for r in rows]

@app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: str, authorization: str | None = Header(default=None)):
    admin(authorization)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        events = [dict(r) for r in conn.execute(
            "SELECT * FROM events WHERE task_id=? ORDER BY id", (task_id,))]
    result = serialize_task(row)
    result["events"] = events
    return result

@app.post("/api/v1/tasks/{task_id}/approve")
def approve_task(task_id: str, authorization: str | None = Header(default=None)):
    admin(authorization)
    now = time.time()
    with db.connect() as conn:
        row = conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        if row["status"] != "pending_approval":
            raise HTTPException(409, "Task is not awaiting approval")
        conn.execute("UPDATE tasks SET status='queued',approved_by='admin',updated_at=? WHERE id=?",
                     (now, task_id))
        add_event(conn, "task.approved", "Approved for worker dispatch", task_id)
    return {"id": task_id, "status": "queued"}

@app.post("/api/v1/tasks/{task_id}/cancel")
def cancel_task(task_id: str, authorization: str | None = Header(default=None)):
    admin(authorization)
    now = time.time()
    with db.connect() as conn:
        row = conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        if row["status"] in {"succeeded", "failed", "cancelled"}:
            raise HTTPException(409, "Task is already terminal")
        conn.execute("UPDATE tasks SET status='cancelled',updated_at=? WHERE id=?", (now, task_id))
        add_event(conn, "task.cancelled", "Cancelled by administrator", task_id)
    return {"id": task_id, "status": "cancelled"}

@app.post("/api/v1/workers/heartbeat")
def heartbeat(body: WorkerHeartbeat, authorization: str | None = Header(default=None)):
    worker(authorization)
    now = time.time()
    with db.connect() as conn:
        existing = conn.execute("SELECT id FROM workers WHERE id=?", (body.worker_id,)).fetchone()
        conn.execute(
            """INSERT INTO workers(id,name,hostname,platform,capabilities,last_seen,status)
            VALUES(?,?,?,?,?,?,'online') ON CONFLICT(id) DO UPDATE SET name=excluded.name,
            hostname=excluded.hostname,platform=excluded.platform,capabilities=excluded.capabilities,
            last_seen=excluded.last_seen,status='online'""",
            (body.worker_id, body.name, body.hostname, body.platform,
             json.dumps(body.capabilities), now))
        if not existing:
            add_event(conn, "worker.registered", "Worker registered: " + body.name,
                      worker_id=body.worker_id)
    return {"status": "ok", "server_time": now}

@app.post("/api/v1/workers/claim")
def claim_task(worker_id: str, authorization: str | None = Header(default=None)):
    worker(authorization)
    with db.connect() as conn:
        registered = conn.execute("SELECT id FROM workers WHERE id=?", (worker_id,)).fetchone()
    if not registered:
        raise HTTPException(403, "Worker must heartbeat before claiming tasks")
    now = time.time()
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        expired = conn.execute(
            "SELECT id,attempt,max_attempts FROM tasks WHERE status='running' AND lease_until<?",
            (now,)).fetchall()
        for row in expired:
            status = "queued" if row["attempt"] < row["max_attempts"] else "failed"
            conn.execute("UPDATE tasks SET status=?,worker_id=NULL,lease_until=NULL,updated_at=? WHERE id=?",
                         (status, now, row["id"]))
            add_event(conn, "task.lease_expired", "Lease expired; moved to " + status, row["id"])
        row = conn.execute(
            "SELECT * FROM tasks WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if row is None:
            conn.execute("COMMIT")
            return {"task": None}
        lease = now + settings.lease_seconds
        conn.execute(
            """UPDATE tasks SET status='running',worker_id=?,lease_until=?,attempt=attempt+1,
            updated_at=? WHERE id=? AND status='queued'""",
            (worker_id, lease, now, row["id"]))
        add_event(conn, "task.claimed", "Claimed by " + worker_id, row["id"], worker_id)
        claimed = conn.execute("SELECT * FROM tasks WHERE id=?", (row["id"],)).fetchone()
        conn.execute("COMMIT")
    return {"task": serialize_task(claimed), "lease_until": lease}

@app.post("/api/v1/workers/renew")
def renew_lease(task_id: str, worker_id: str, authorization: str | None = Header(default=None)):
    worker(authorization)
    now = time.time()
    with db.connect() as conn:
        row = conn.execute("SELECT status,worker_id FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        if row["status"] != "running" or row["worker_id"] != worker_id:
            raise HTTPException(409, "Worker does not own an active task lease")
        lease = now + settings.lease_seconds
        conn.execute("UPDATE tasks SET lease_until=?,updated_at=? WHERE id=?", (lease, now, task_id))
    return {"lease_until": lease}

@app.get("/api/v1/workers/tasks/{task_id}/state")
def worker_task_state(task_id: str, worker_id: str,
                      authorization: str | None = Header(default=None)):
    worker(authorization)
    with db.connect() as conn:
        row = conn.execute("SELECT status,worker_id FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        if row["worker_id"] != worker_id:
            raise HTTPException(403, "Task belongs to a different worker")
        return {"status": row["status"]}

@app.post("/api/v1/tasks/{task_id}/complete")
def complete_task(task_id: str, body: TaskCompletion,
                  authorization: str | None = Header(default=None)):
    worker(authorization)
    now = time.time()
    with db.connect() as conn:
        row = conn.execute("SELECT status,worker_id FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        if row["status"] != "running":
            raise HTTPException(409, "Task is not running")
        if row["worker_id"] != body.worker_id:
            raise HTTPException(403, "Task is assigned to a different worker")
        conn.execute(
            """UPDATE tasks SET status=?,result=?,error=?,lease_until=NULL,updated_at=?
            WHERE id=? AND worker_id=?""",
            (body.status, body.result, body.error, now, task_id, body.worker_id))
        add_event(conn, "task." + body.status, body.error or "Worker reported completion",
                  task_id, body.worker_id)
    return {"id": task_id, "status": body.status}
