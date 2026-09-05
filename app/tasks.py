import uuid
from sqlalchemy.exc import OperationalError
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import Job, JobStatus, Operation
from processing import image_ops

@celery_app.task(autoretry_for=(OperationalError,),max_retries=3, retry_backoff=True)
def process_job(job_id: str):
    db = SessionLocal()
    try:
        job = db.get(Job, uuid.UUID(job_id))
        job.status = JobStatus.processing
        db.commit()

        try:
            if job.operation == Operation.resize:
                output_path = image_ops.resize(job.source_path, job.target_width, job.target_height)
            elif job.operation == Operation.thumbnail:
                output_path = image_ops.thumbnail(job.source_path, job.target_width, job.target_height)
            elif job.operation == Operation.convert:
                output_path = image_ops.convert(job.source_path, job.target_format.value)

            job.output_path = output_path
            job.status = JobStatus.done
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.failed
        
        db.commit()
    finally:
        db.close()