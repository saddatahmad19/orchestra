from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    prompt: str = Field(min_length=1, max_length=50000)
    engine: str = Field(default="opencode", min_length=1, max_length=80)
    project_path: str | None = Field(default=None, max_length=1000)
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
