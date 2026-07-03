# Getting Started with dehelpers

`dehelpers` is a lightweight Python toolkit for data engineering pipelines. It wraps battle-tested libraries — `requests`, `SQLAlchemy`, and Python's built-in `logging` — into a small set of production-hardened utilities so you can focus on moving and transforming data instead of rebuilding infrastructure.

If you have ever copied the same retry logic, the same database setup, or the same logging configuration across multiple ETL scripts, this library is for you.

---

## Who Is This For?

- Data engineers writing batch ETL scripts or Airflow DAGs.
- Backend developers who fetch from REST APIs and load into PostgreSQL.
- Anyone tired of copying `utils.py` between projects.

---

## Prerequisites

- **Python 3.10 or later**
- **PostgreSQL** (optional — only needed if you use `DatabaseManager` against a real database)

---

## Install

```bash
pip install dehelpers
```

See [Installation](installation.md) for optional extras like Pandas DataFrame support.

---

## Your First Pipeline

Here is a minimal, end-to-end pipeline that fetches data from a public REST API, logs the process with structured JSON, and stores results in PostgreSQL — all in under 25 lines of application code.

```python
"""Minimal dehelpers pipeline: fetch → log → store."""

import sys
from dehelpers import ResilientClient, DatabaseManager, get_logger, LogContext

# 1. Structured JSON logger — secrets are auto-redacted
logger = get_logger("my_first_pipeline", job_id="getting-started")

# 2. Resilient HTTP client — retries, backoff, and timeouts built in
client = ResilientClient()

# 3. PostgreSQL connection — reads DATABASE_URL from environment
#    (skip this block if you just want to test the HTTP client)
try:
    db = DatabaseManager()
except Exception:
    logger.warning("No DATABASE_URL set — skipping database steps")
    db = None

# 4. Fetch data
resp = client.get("https://jsonplaceholder.typicode.com/users")
users = resp.json()
logger.info("Fetched users", extra={"count": len(users)})

# 5. Store each user (if database is available)
if db is not None:
    for user in users:
        with LogContext(request_id=f"user-{user['id']}"):
            with db.session() as session:
                session.execute(
                    "INSERT INTO users (id, name, email) "
                    "VALUES (:id, :name, :email) "
                    "ON CONFLICT (id) DO UPDATE "
                    "SET name = EXCLUDED.name, email = EXCLUDED.email",
                    {"id": user["id"], "name": user["name"], "email": user["email"]},
                )
            logger.info("Stored user", extra={"name": user["name"]})
    db.dispose()

client.close()
logger.info("Pipeline complete")
```

**What happens behind the scenes:**

| Step | What `dehelpers` does for you |
|---|---|
| `get_logger(...)` | Creates a JSON formatter on `stderr` with automatic secret redaction |
| `ResilientClient()` | Wraps `requests.Session` with bounded retries, exponential backoff, jitter, and per-request timeouts |
| `DatabaseManager()` | Creates a SQLAlchemy engine with connection pooling, pre-ping health checks, and auto-rollback on failure |
| `LogContext(...)` | Injects `request_id` into every log record emitted inside the block |

---

## Where to Go Next

| Topic | Link |
|---|---|
| All install options and extras | [Installation](installation.md) |
| Full API docs for every class and function | [API Reference](api-reference.md) |
| Architecture, design philosophy, and diagrams | [Architecture](architecture.md) |
| Runnable example scripts | [Examples](examples/) |
| Common questions and troubleshooting | [FAQ](faq.md) |
