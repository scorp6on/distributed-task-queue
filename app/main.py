import uuid
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Job
from app.schemas import JobParams, JobRead

MEDIA_DIR = Path("media/uploads")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

@app.post("/jobs", response_model=JobRead, status_code=201)
async def create_job(
    params: Annotated[JobParams, Form()],
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
):
    job_id = uuid.uuid4()
    suffix = Path(file.filename).suffix
    dest = MEDIA_DIR / f"{job_id}{suffix}"

    content = await file.read()
    dest.write_bytes(content)

    job = Job(
        id=job_id,
        operation=params.operation,
        source_path=str(dest),
        target_width=params.target_width,
        target_height=params.target_height,
        target_format=params.target_format,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@app.get("/jobs/{job_id}", response_model=JobRead)
def get_job(
    job_id:uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job Not Found")
    return job