# Frequently Asked Questions

## General

### What Python versions are supported?

Python 3.10, 3.11, and 3.12. The CI pipeline tests all three versions on every commit.

### Is this library production-ready?

Version 0.1.0 is stable for its documented scope: batch ETL scripts, Airflow DAGs, and containerised data pipelines. The API surface is small and well-tested. See [Architecture — Boundaries](architecture.md#boundaries) for what the library is and is not designed for.

---

## HTTP Client

### How do I customise the retry behaviour?

Pass a `RetryPolicy` to `ResilientClient`:

```python
from dehelpers import ResilientClient, RetryPolicy

policy = RetryPolicy(
    max_retries=5,
    backoff_base=2.0,
    total_timeout=300.0,
    retry_non_idempotent=True,
)
client = ResilientClient(retry_policy=policy)
```

See [API Reference — RetryPolicy](api-reference.md#retrypolicy) for the full parameter list.

### Does the client respect `Retry-After` headers?

Yes. When an API returns HTTP 429 with a `Retry-After` header, `ResilientClient` uses that value as the delay instead of computing exponential backoff.

### Why are POST requests not retried by default?

POST requests are not idempotent — retrying them could create duplicate records. Set `retry_non_idempotent=True` in your `RetryPolicy` only when you know the endpoint is safe to retry (e.g. it uses an idempotency key or upsert logic).

---

## Database

### How do I connect to PostgreSQL?

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/mydb"
```

Or pass the DSN directly:

```python
db = DatabaseManager(dsn="postgresql+psycopg://user:password@host:5432/mydb")
```

### Why `psycopg` and not `psycopg2`?

`psycopg` (version 3) is the actively maintained PostgreSQL driver for Python. It supports async, connection pooling, and binary protocol natively. `psycopg2` is in maintenance mode. The `[binary]` extra bundles `libpq` so you don't need to install system packages.

### What happens if a transaction fails?

The `session()` context manager automatically rolls back the transaction on any exception and closes the session in the `finally` block. You never need to call `rollback()` manually.

```python
with db.session() as session:
    session.execute("INSERT INTO ...")
    raise ValueError("Something went wrong")
    # ← Transaction is automatically rolled back here
```

---

## Airflow / Multiprocessing

### Is `DatabaseManager` safe to use with Airflow?

Yes, but with one important caveat: **SQLAlchemy connection pools must not be shared across forked processes.**

You have two options:

1. **Create the `DatabaseManager` inside each worker task** (recommended):
   ```python
   @task
   def my_airflow_task():
       db = DatabaseManager()  # Fresh pool per worker
       # ... use db ...
       db.dispose()
   ```

2. **Call `db.dispose()` before forking:**
   ```python
   db = DatabaseManager()
   db.dispose()  # Clears the pool before fork
   # Now safe to fork
   ```

---

## Logging & Security

### Which keys are redacted by default?

The following keys trigger automatic redaction (case-insensitive substring matching):

`password`, `secret`, `token`, `api_key`, `authorization`, `dsn`, `connection_string`, `credential`, `passphrase`, `private_key`, `client_secret`

A key like `db_password` or `my_api_key_v2` will match because it contains the sensitive substring.

### How do I add custom keys to the redaction list?

Use `redact_dict` with `extra_sensitive_keys`:

```python
from dehelpers._redact import redact_dict

result = redact_dict(
    {"my_custom_secret": "value", "host": "localhost"},
    extra_sensitive_keys=frozenset({"my_custom_secret"}),
)
# → {"my_custom_secret": "***REDACTED***", "host": "localhost"}
```

### Are URL path segments redacted?

**No.** Only query parameter values are redacted. Never embed secrets in URL paths:

```
# BAD — token in path (not redacted)
https://api.example.com/v1/token/abc123/data

# GOOD — token in query parameter (redacted)
https://api.example.com/v1/data?token=abc123

# BEST — token in header (never logged)
headers={"Authorization": "Bearer abc123"}
```

---

## Roadmap

### Is async support planned?

Yes. `AsyncResilientClient` is planned for v1.2. It will use `httpx` or `aiohttp` for async HTTP and will follow the same `RetryPolicy` configuration. This is not yet implemented.

### What about cursor-based pagination?

Cursor-based pagination (`CursorPagination`) is planned for v1.1. The current `NextLinkPagination` strategy follows a URL in the JSON response body.

### Will there be schema validation?

Schema validation via `pydantic` integration is a conceptual goal for v2.0. No implementation timeline has been set.

---

## Contributing

### How do I run the tests?

```bash
# Unit tests (no PostgreSQL required)
pip install -e ".[dev,dataframe]"
pytest -v --tb=short -m "not postgres"

# PostgreSQL integration tests
docker run -d --name pg-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16
DATABASE_URL="postgresql+psycopg://postgres:test@localhost:5432/postgres" \
    pytest -m postgres -v
```

### Where do I report bugs?

Open an issue on [GitHub](https://github.com/shard-c6/dehelpers/issues). Include steps to reproduce, expected behaviour, and any relevant traceback or log output.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full contribution guidelines.
