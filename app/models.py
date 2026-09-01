from datetime import datetime
import uuid
import enum
from sqlalchemy import Enum as SqlEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"

class Operation(str, enum.Enum):
    resize = "resize"
    thumbnail = "thumbnail"
    convert = "convert"

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[JobStatus] = mapped_column(SqlEnum(JobStatus), default=JobStatus.queued)
    operation: Mapped[Operation] = mapped_column(SqlEnum(Operation))
    source_path: Mapped[str]
    target_width: Mapped[int | None]
    target_height: Mapped[int | None]
    target_format: Mapped[str | None]
    output_path: Mapped[str | None]
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())