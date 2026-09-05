import uuid


def test_create_job_resize_happy_path(client, sample_image_bytes):
    r = client.post(
        "/jobs",
        data={"operation": "resize", "target_width": "400", "target_height": "300"},
        files={"file": ("test.png", sample_image_bytes(), "image/png")},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["operation"] == "resize"
    assert body["status"] == "queued"
    assert body["target_width"] == 400
    assert body["target_height"] == 300


def test_job_is_actually_processed_by_the_eager_task(client, sample_image_bytes):
    r = client.post(
        "/jobs",
        data={"operation": "resize", "target_width": "400", "target_height": "300"},
        files={"file": ("test.png", sample_image_bytes(), "image/png")},
    )
    job_id = r.json()["id"]

    r2 = client.get(f"/jobs/{job_id}")

    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "done"
    assert body["output_path"] is not None
    assert body["error"] is None


def test_create_job_convert_without_format_is_rejected(client, sample_image_bytes):
    r = client.post(
        "/jobs",
        data={"operation": "convert"},
        files={"file": ("test.png", sample_image_bytes(), "image/png")},
    )

    assert r.status_code == 422


def test_create_job_resize_missing_height_is_rejected(client, sample_image_bytes):
    r = client.post(
        "/jobs",
        data={"operation": "resize", "target_width": "400"},
        files={"file": ("test.png", sample_image_bytes(), "image/png")},
    )

    assert r.status_code == 422


def test_create_job_with_corrupt_image_ends_up_failed(client):
    r = client.post(
        "/jobs",
        data={"operation": "resize", "target_width": "400", "target_height": "300"},
        files={"file": ("bad.png", b"not a real image", "image/png")},
    )
    job_id = r.json()["id"]

    r2 = client.get(f"/jobs/{job_id}")

    assert r2.json()["status"] == "failed"
    assert r2.json()["error"] is not None


def test_get_job_not_found_returns_404(client):
    r = client.get(f"/jobs/{uuid.uuid4()}")

    assert r.status_code == 404
