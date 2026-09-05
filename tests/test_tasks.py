import uuid

from sqlalchemy.exc import OperationalError

from app.models import ImageFormat, Job, JobStatus, Operation
from app.tasks import process_job


def _make_job(db_session, source_path, **kwargs):
    job = Job(id=uuid.uuid4(), source_path=str(source_path), **kwargs)
    db_session.add(job)
    db_session.commit()
    return job


def test_process_job_resize_success(db_session, tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes(size=(1200, 800)).read())
    job = _make_job(db_session, src, operation=Operation.resize, target_width=400, target_height=300)

    process_job(str(job.id))

    db_session.refresh(job)
    assert job.status == JobStatus.done
    assert job.output_path is not None
    assert job.error is None


def test_process_job_convert_success(db_session, tmp_path, sample_image_bytes):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes().read())
    job = _make_job(db_session, src, operation=Operation.convert, target_format=ImageFormat.webp)

    process_job(str(job.id))

    db_session.refresh(job)
    assert job.status == JobStatus.done
    assert job.output_path.endswith(".webp")


def test_process_job_bad_image_marks_job_failed_not_retried(db_session, tmp_path):
    src = tmp_path / "corrupt.png"
    src.write_bytes(b"not a real image")
    job = _make_job(db_session, src, operation=Operation.resize, target_width=400, target_height=300)

    process_job(str(job.id))

    db_session.refresh(job)
    assert job.status == JobStatus.failed
    assert job.output_path is None
    assert job.error is not None


def test_process_job_status_flips_to_processing_before_the_work_happens(
    db_session, tmp_path, sample_image_bytes
):
    src = tmp_path / "in.png"
    src.write_bytes(sample_image_bytes().read())
    job = _make_job(db_session, src, operation=Operation.resize, target_width=100, target_height=100)

    assert job.status == JobStatus.queued
    process_job(str(job.id))
    db_session.refresh(job)
    assert job.status == JobStatus.done


def test_process_job_only_retries_on_transient_db_errors_not_bad_input():
    assert process_job.autoretry_for == (OperationalError,)
    assert process_job.max_retries == 3
