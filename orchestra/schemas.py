from pydantic import BaseModel, Field, field_validator

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4000)
    repository_url: str | None = Field(default=None, max_length=1000)
    default_engine: str = Field(default="opencode", min_length=1, max_length=80)
    instructions: str = Field(default="", max_length=20000)
    node_paths: dict[str, str] = Field(default_factory=dict, max_length=30)

    @field_validator("node_paths")
    @classmethod
    def validate_paths(cls, value):
        for node, path in value.items():
            if not node.strip() or not path.strip() or len(path) > 1000:
                raise ValueError("Each node path requires a node ID and an absolute path")
            if not path.startswith("/"):
                raise ValueError("Project paths must be absolute POSIX paths")
        return value

class ProjectUpdate(ProjectCreate):
    pass

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    prompt: str = Field(min_length=1, max_length=50000)
    engine: str | None = Field(default=None, max_length=80)
    project_id: str | None = Field(default=None, max_length=64)
    project_path: str | None = Field(default=None, max_length=1000)
    target_worker_id: str | None = Field(default=None, max_length=100)
    approval_required: bool = True
    max_attempts: int = Field(default=2, ge=1, le=5)

class WorkerHeartbeat(BaseModel):
    worker_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=120)
    hostname: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=120)
    capabilities: list[str] = Field(default_factory=list, max_length=100)

class TaskCompletion(BaseModel):
    worker_id: str = Field(min_length=1, max_length=100)
    status: str
    result: str | None = Field(default=None, max_length=100000)
    error: str | None = Field(default=None, max_length=20000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value not in {"succeeded", "failed"}:
            raise ValueError("status must be succeeded or failed")
        return value
