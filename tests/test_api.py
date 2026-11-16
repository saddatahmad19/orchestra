import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(monkeypatch):
    tmp = tempfile.TemporaryDirectory()
    monkeypatch.setenv("ORCHESTRA_ADMIN_TOKEN", "a" * 40)
    monkeypatch.setenv("ORCHESTRA_WORKER_TOKEN", "w" * 40)
    monkeypatch.setenv("ORCHESTRA_DATABASE", str(Path(tmp.name) / "test.db"))
    import orchestra.main as module
    module.settings = module.Settings.from_env()
    module.db = module.Database(module.settings.database)
    with TestClient(module.app) as test_client:
        yield test_client
    tmp.cleanup()

def admin():
    return {"Authorization": "Bearer " + "a" * 40}

def worker():
    return {"Authorization": "Bearer " + "w" * 40}

def register(client, worker_id="thinkpad"):
    return client.post("/api/v1/workers/heartbeat", headers=worker(), json={
        "worker_id": worker_id, "name": worker_id, "capabilities": ["opencode"]
    })

def test_health_is_public(client):
    assert client.get("/health").json()["status"] == "ok"

def test_admin_auth_required(client):
    assert client.get("/api/v1/tasks").status_code == 401

def test_approval_prevents_claim_until_approved(client):
    created = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Test", "prompt": "Do not run without approval"
    })
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["status"] == "pending_approval"
    register(client)
    assert client.post("/api/v1/workers/claim?worker_id=thinkpad", headers=worker()).json()["task"] is None
    assert client.post(f"/api/v1/tasks/{task_id}/approve", headers=admin()).status_code == 200
    claim = client.post("/api/v1/workers/claim?worker_id=thinkpad", headers=worker()).json()
    assert claim["task"]["id"] == task_id

def test_completion_requires_assigned_worker(client):
    task = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Run", "prompt": "safe", "approval_required": False
    }).json()
    register(client)
    client.post("/api/v1/workers/claim?worker_id=thinkpad", headers=worker())
    wrong = client.post(f"/api/v1/tasks/{task['id']}/complete", headers=worker(),
        json={"worker_id":"other","status":"succeeded","result":"fake"})
    assert wrong.status_code == 403
    good = client.post(f"/api/v1/tasks/{task['id']}/complete", headers=worker(),
        json={"worker_id":"thinkpad","status":"succeeded","result":"verified"})
    assert good.status_code == 200
    assert client.get(f"/api/v1/tasks/{task['id']}", headers=admin()).json()["status"] == "succeeded"

def test_terminal_task_cannot_be_cancelled_twice(client):
    task = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Cancel", "prompt": "none", "approval_required": False
    }).json()
    assert client.post(f"/api/v1/tasks/{task['id']}/cancel", headers=admin()).status_code == 200
    assert client.post(f"/api/v1/tasks/{task['id']}/cancel", headers=admin()).status_code == 409


def test_unregistered_worker_cannot_claim(client):
    response = client.post("/api/v1/workers/claim?worker_id=unknown", headers=worker())
    assert response.status_code == 403

def test_worker_can_renew_its_own_lease(client):
    task = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Lease", "prompt": "renew", "approval_required": False
    }).json()
    register(client)
    client.post("/api/v1/workers/claim?worker_id=thinkpad", headers=worker())
    renewed = client.post("/api/v1/workers/renew?task_id=" + task["id"] + "&worker_id=thinkpad",
                          headers=worker())
    assert renewed.status_code == 200
    wrong = client.post("/api/v1/workers/renew?task_id=" + task["id"] + "&worker_id=other",
                        headers=worker())
    assert wrong.status_code == 409


def test_project_paths_route_only_to_selected_worker(client):
    register(client, "thinkpad-x1")
    register(client, "pi5")
    project = client.post("/api/v1/projects", headers=admin(), json={
        "name": "Lintra",
        "default_engine": "opencode",
        "instructions": "Use pnpm and run tests.",
        "node_paths": {
            "thinkpad-x1": "/home/saddat/projects/lintra",
            "pi5": "/home/saddat/workspaces/lintra"
        }
    })
    assert project.status_code == 201
    project_id = project.json()["id"]
    created = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Inspect Lintra",
        "prompt": "Review the project and report risks.",
        "project_id": project_id,
        "target_worker_id": "pi5",
        "approval_required": False
    })
    assert created.status_code == 201
    assert client.post("/api/v1/workers/claim?worker_id=thinkpad-x1",
                       headers=worker()).json()["task"] is None
    claimed = client.post("/api/v1/workers/claim?worker_id=pi5",
                          headers=worker()).json()["task"]
    assert claimed["project_path"] == "/home/saddat/workspaces/lintra"
    assert claimed["engine"] == "opencode"
    assert "Use pnpm and run tests." in claimed["prompt"]


def test_project_rejects_missing_node_path(client):
    project = client.post("/api/v1/projects", headers=admin(), json={
        "name": "Missing mapping",
        "node_paths": {"thinkpad-x1": "/home/saddat/projects/missing"}
    }).json()
    response = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Must not dispatch",
        "prompt": "Run this",
        "project_id": project["id"],
        "target_worker_id": "pi5"
    })
    assert response.status_code == 422
    assert "No filesystem path is configured" in response.json()["detail"]


def test_project_cannot_be_deleted_after_tasks_reference_it(client):
    register(client, "thinkpad-x1")
    project = client.post("/api/v1/projects", headers=admin(), json={
        "name": "Retained project",
        "node_paths": {"thinkpad-x1": "/tmp/project"}
    }).json()
    task = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Keep project reference",
        "prompt": "Do not execute",
        "project_id": project["id"],
        "target_worker_id": "thinkpad-x1"
    })
    assert task.status_code == 201
    deleted = client.delete("/api/v1/projects/" + project["id"], headers=admin())
    assert deleted.status_code == 409


def test_project_paths_route_only_to_selected_worker(client):
    register(client, "thinkpad-x1")
    register(client, "pi5")
    project = client.post("/api/v1/projects", headers=admin(), json={
        "name": "Lintra",
        "default_engine": "opencode",
        "instructions": "Use pnpm and run tests.",
        "node_paths": {
            "thinkpad-x1": "/home/saddat/projects/lintra",
            "pi5": "/home/saddat/workspaces/lintra"
        }
    })
    assert project.status_code == 201
    created = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Inspect Lintra",
        "prompt": "Review the project and report risks.",
        "project_id": project.json()["id"],
        "target_worker_id": "pi5",
        "approval_required": False
    })
    assert created.status_code == 201
    assert client.post("/api/v1/workers/claim?worker_id=thinkpad-x1",
                       headers=worker()).json()["task"] is None
    claimed = client.post("/api/v1/workers/claim?worker_id=pi5",
                          headers=worker()).json()["task"]
    assert claimed["project_path"] == "/home/saddat/workspaces/lintra"
    assert claimed["engine"] == "opencode"
    assert "Use pnpm and run tests." in claimed["prompt"]


def test_project_rejects_missing_node_path(client):
    project = client.post("/api/v1/projects", headers=admin(), json={
        "name": "Missing mapping",
        "node_paths": {"thinkpad-x1": "/home/saddat/projects/missing"}
    }).json()
    response = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Must not dispatch",
        "prompt": "Run this",
        "project_id": project["id"],
        "target_worker_id": "pi5"
    })
    assert response.status_code == 422
    assert "No filesystem path is configured" in response.json()["detail"]


def test_project_cannot_be_deleted_after_tasks_reference_it(client):
    register(client, "thinkpad-x1")
    project = client.post("/api/v1/projects", headers=admin(), json={
        "name": "Retained project",
        "node_paths": {"thinkpad-x1": "/tmp/project"}
    }).json()
    task = client.post("/api/v1/tasks", headers=admin(), json={
        "title": "Keep project reference",
        "prompt": "Do not execute",
        "project_id": project["id"],
        "target_worker_id": "thinkpad-x1"
    })
    assert task.status_code == 201
    deleted = client.delete("/api/v1/projects/" + project["id"], headers=admin())
    assert deleted.status_code == 409
