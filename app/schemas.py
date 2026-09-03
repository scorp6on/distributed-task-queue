from pydantic import BaseModel, model_validator, ConfigDict, Field
from app.models import Operation, JobStatus, ImageFormat
from datetime import datetime
import uuid

class JobParams(BaseModel):
    operation: Operation
    target_width: int | None = Field(default=None, gt=0)
    target_height: int | None = Field(default=None, gt=0)
    target_format: ImageFormat | None = None

    @model_validator(mode="after")
    def check_params(self):
        if self.operation == Operation.resize:
            if self.target_width is None or self.target_height is None:
                raise ValueError("resize requires target_width and target_height")
        elif self.operation == Operation.thumbnail:
            if self.target_width is None and self.target_height is None:
                raise ValueError("thumbnail requires target_width or target_height")
        elif self.operation == Operation.convert:
            if self.target_format is None:
                raise ValueError("convert requires target_format")
        return self
    
class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: JobStatus
    operation: Operation
    source_path: str
    target_width: int | None
    target_height: int | None
    target_format: ImageFormat | None
    output_path: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime