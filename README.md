# Distributed Task Queue

An async job-processing service: submit an image, get a job id back immediately,
and poll for the result while a separate worker does the actual work. Built to
practice the pattern used by any "slow work happens off the request thread"
system — image processing is just the one task type in scope here.

## How it works

```
client
  │  POST /jobs (multipart: file + operation + params)
  ▼
FastAPI ──writes──▶ Postgres (job row, status=queued)
  │
  │  enqueues (job id only)
  ▼
Redis ──consumed by──▶ Celery worker
                          │
                          │  status=processing
                          ▼
                       Pillow (resize / thumbnail / convert)
                          │
                          │  status=done + output_path, or
                          │  status=failed + error
                          ▼
                       Postgres

client
  │  GET /jobs/{id}
  ▼
FastAPI ──reads──▶ Postgres
```

The API and the worker are separate processes that only communicate through
Postgres (job state) and Redis (the queue) — the API never talks to Pillow
directly, and the worker never talks to HTTP.

## Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — HTTP API
- **[Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/docs/latest/)** — background job queue
- **[SQLAlchemy](https://docs.sqlalchemy.org/) + [Postgres](https://www.postgresql.org/docs/)** — job storage
- **[Pillow](https://pillow.readthedocs.io/)** — the actual image operations
- **[Flower](https://flower.readthedocs.io/)** — queue/worker monitoring dashboard
- **[Docker Compose](https://docs.docker.com/compose/)** — runs all five services together
- **[pytest](https://docs.pytest.org/)** — unit + integration tests, no live broker required

## API

### `POST /jobs`

Multipart form:

| field | required | notes |
|---|---|---|
| `file` | yes | the image to process |
| `operation` | yes | `resize` \| `thumbnail` \| `convert` |
| `target_width` | conditional | required for `resize`; at least one of width/height required for `thumbnail` |
| `target_height` | conditional | same as above |
| `target_format` | conditional | required for `convert` — `png` \| `jpeg` \| `webp` |

Returns `201` with the created job. A missing required field for the chosen
operation returns `422`.

### `GET /jobs/{id}`

Returns the job's current state — `status`, and once finished, `output_path`
or `error`. Returns `404` if the id doesn't exist.

```json
{
  "id": "97539209-c3b7-4c40-8389-d0b8d4da42aa",
  "status": "done",
  "operation": "resize",
  "source_path": "media/uploads/97539209-....png",
  "target_width": 800,
  "target_height": 600,
  "target_format": null,
  "output_path": "media/outputs/97539209-....png",
  "error": null,
  "created_at": "2026-09-04T20:07:42.849803",
  "updated_at": "2026-09-04T20:07:42.849803"
}
```

## Running it

```bash
docker compose up --build
```

Brings up Postgres, Redis, the API (`:8000`), a Celery worker, and Flower
(`:5555`). Interactive API docs at `http://localhost:8000/docs`.

## Tests

```bash
pytest -v
```

Runs against a dedicated `taskq_test` Postgres database with Celery in eager
mode (`task_always_eager=True`) — no Redis, no worker process, no Docker
required. ~3.5 seconds for the full suite.

## Design notes

- **Failures are data, not exceptions that escape.** A bad/corrupt image
  fails the job (`status=failed`, `error` set) — it doesn't crash the worker.
- **Retries are scoped to transient infra failures only** (a dropped DB
  connection), via Celery's built-in `autoretry_for`/`max_retries`. A corrupt
  image fails identically on every attempt, so retrying it would only waste
  time — that failure path is handled separately and doesn't retry.
- **The image-processing functions know nothing about jobs, Celery, or the
  database** (`processing/image_ops.py`) — they're plain functions over file
  paths, which makes them unit-testable with zero infrastructure.
- Scope was deliberately reduced for a two-week build (one task type, no
  Kubernetes, no custom dead-letter queue). Cut items are tracked, not
  silently dropped.
