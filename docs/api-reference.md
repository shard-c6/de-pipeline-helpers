# API Reference

Complete reference for every public class, function, and exception in `dehelpers` v0.1.0.

All symbols listed here are importable directly from `dehelpers`:

```python
from dehelpers import (
    ResilientClient, RetryPolicy, NextLinkPagination,
    DatabaseManager,
    get_logger, LogContext,
    DPHError, RetryError, PaginationError, DatabaseError,
)
```

---

## `dehelpers.api` — Resilient HTTP Client

### `RetryPolicy`

```python
@dataclass(frozen=True)
class RetryPolicy
```

Immutable configuration for retry behaviour. All fields have sensible defaults.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_retries` | `int` | `3` | Maximum number of *retries* (total attempts = `max_retries + 1`) |
| `backoff_base` | `float` | `1.0` | Base delay in seconds for exponential backoff |
| `backoff_max` | `float` | `30.0` | Maximum delay cap in seconds |
| `jitter` | `bool` | `True` | Adds random jitter to prevent thundering-herd effects |
| `total_timeout` | `float` | `120.0` | Wall-clock cap in seconds from the start of the first attempt |
| `retryable_statuses` | `frozenset[int]` | `{429, 500, 502, 503, 504}` | HTTP status codes that trigger a retry |
| `retry_non_idempotent` | `bool` | `False` | If `True`, retries POST/PUT/DELETE (default: only GET/HEAD/OPTIONS) |
| `connect_timeout` | `float` | `5.0` | Per-request TCP connect timeout in seconds |
| `read_timeout` | `float` | `30.0` | Per-request read timeout in seconds |

**Example:**

```python
from dehelpers import RetryPolicy

# More aggressive: 5 retries, retry POST, 3-minute total timeout
policy = RetryPolicy(
    max_retries=5,
    retry_non_idempotent=True,
    total_timeout=180.0,
)
```

---

### `NextLinkPagination`

```python
class NextLinkPagination(
    next_key: str = "next",
    results_key: str = "results",
    max_pages: int = 100,
)
```

Pagination strategy that follows a URL in the JSON response to fetch subsequent pages.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `next_key` | `str` | `"next"` | Key in the JSON response containing the next page URL |
| `results_key` | `str` | `"results"` | Key in the JSON response containing the list of items |
| `max_pages` | `int` | `100` | Safety limit on the number of pages to fetch |

**Example:**

```python
from dehelpers import NextLinkPagination

# API returns items under "data" and next URL under "pagination.next_url"
pag = NextLinkPagination(next_key="next_url", results_key="data", max_pages=50)
```

---

### `ResilientClient`

```python
class ResilientClient(
    retry_policy: RetryPolicy | None = None,
    logger: logging.Logger | None = None,
)
```

HTTP client wrapping `requests.Session` with automatic retries, exponential backoff, jitter, and pagination support.

Supports use as a context manager:

```python
with ResilientClient() as client:
    resp = client.get("https://api.example.com/data")
```

#### Methods

##### `get(url, **kwargs) → requests.Response`

Send a GET request with retry protection. All `**kwargs` are forwarded to `requests.Session.request()`.

##### `post(url, **kwargs) → requests.Response`

Send a POST request with retry protection.

##### `put(url, **kwargs) → requests.Response`

Send a PUT request with retry protection.

##### `delete(url, **kwargs) → requests.Response`

Send a DELETE request with retry protection.

##### `request(method, url, **kwargs) → requests.Response`

Core method. Sends an HTTP request with bounded retries and backoff.

**Raises:**
- `RetryError` — when all retry attempts are exhausted or `total_timeout` is exceeded. The original exception is preserved as `__cause__`.
- `requests.HTTPError` — on non-retryable HTTP errors (e.g. 400, 401, 403, 404).

**Behaviour details:**
- Respects `Retry-After` header on HTTP 429 responses.
- URL query parameters containing sensitive keys are redacted in log output.
- Non-idempotent methods (POST, PUT, DELETE) are **not retried by default** — set `retry_non_idempotent=True` in `RetryPolicy` to opt in.

##### `paginate(url, pagination=None, **kwargs) → Iterator[dict]`

Yield individual items across paginated responses.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | — | Initial page URL |
| `pagination` | `NextLinkPagination \| None` | `None` | Pagination strategy (defaults to `NextLinkPagination()`) |
| `**kwargs` | | | Extra keyword arguments forwarded to each GET request |

**Yields:** `dict` — individual items from each page.

**Raises:** `PaginationError` — on any failure. `PaginationError.collected_items` contains items fetched before the failure.

##### `close() → None`

Close the underlying `requests.Session`.

**Example:**

```python
from dehelpers import ResilientClient, RetryPolicy

client = ResilientClient(retry_policy=RetryPolicy(max_retries=5))

# Simple GET
resp = client.get("https://api.example.com/users")
print(resp.json())

# Paginate through all items
for item in client.paginate("https://api.example.com/items"):
    process(item)

client.close()
```

---

## `dehelpers.db` — Database Manager

### `DatabaseManager`

```python
class DatabaseManager(
    dsn: str | None = None,
    *,
    pool_size: int = 5,
    max_overflow: int = 2,
    pool_recycle: int = 1800,
    pool_pre_ping: bool = True,
    pool_timeout: int = 30,
)
```

PostgreSQL connection manager with safe pooling defaults built on SQLAlchemy 2.0.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `dsn` | `str \| None` | `None` | SQLAlchemy connection URL. Falls back to `DATABASE_URL` env var |
| `pool_size` | `int` | `5` | Persistent connections in the pool |
| `max_overflow` | `int` | `2` | Extra connections beyond `pool_size` |
| `pool_recycle` | `int` | `1800` | Seconds before a connection is recycled |
| `pool_pre_ping` | `bool` | `True` | Health-check connections before checkout |
| `pool_timeout` | `int` | `30` | Seconds to wait for a pool connection |

Supports use as a context manager (calls `dispose()` on exit):

```python
with DatabaseManager() as db:
    rows = db.execute("SELECT 1")
```

#### Methods

##### `session() → _SessionContext`

Return a context manager that yields a SQLAlchemy `Session`. Auto-commits on clean exit and auto-rolls-back on exception.

```python
with db.session() as session:
    session.execute(text("INSERT INTO logs (msg) VALUES (:m)"), {"m": "hello"})
    # Commits automatically if no exception is raised
```

##### `execute(sql, params=None) → list[Row]`

Execute SQL and return all rows. The connection is returned to the pool immediately after.

| Parameter | Type | Description |
|---|---|---|
| `sql` | `str` | SQL string (use `:param` style placeholders) |
| `params` | `dict[str, Any] \| None` | Bind parameters |

**Returns:** `list[Row]` — each Row supports both index and attribute access.

**Raises:** `DatabaseError` on query failure.

##### `fetch_one(sql, params=None) → Row | None`

Execute SQL and return the first row, or `None` if the result set is empty.

**Raises:** `DatabaseError` on query failure.

##### `to_dataframe(sql, params=None) → pandas.DataFrame`

Execute SQL and return the result as a Pandas DataFrame.

**Requires:** the `[dataframe]` extra (`pip install dehelpers[dataframe]`).

**Raises:**
- `ImportError` — if `pandas` is not installed.
- `DatabaseError` — on query failure.

##### `dispose() → None`

Dispose the engine and close all pooled connections.

##### `__repr__() → str`

Returns a string with the DSN **redacted** for safe logging.

```python
>>> repr(db)
"DatabaseManager(dsn='postgresql+psycopg://user:***REDACTED***@host/db')"
```

---

## `dehelpers.logger` — Structured JSON Logger

### `get_logger`

```python
def get_logger(
    name: str,
    *,
    job_id: str | None = None,
    level: int = logging.INFO,
) → logging.Logger
```

Return a stdlib `logging.Logger` with JSON formatting and automatic secret redaction.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Logger name (typically the module or pipeline name) |
| `job_id` | `str \| None` | `None` | Default job identifier injected into every record |
| `level` | `int` | `logging.INFO` | Logging level |

**Returns:** A configured logger that writes JSON to `stderr`.

Every log record is emitted as a single JSON line with this schema:

```json
{
  "timestamp": "2026-07-02T11:43:50.123456+00:00",
  "level": "INFO",
  "message": "Fetched 200 rows",
  "module": "db",
  "function": "execute_query",
  "job_id": "etl-daily-sales",
  "request_id": null,
  "error": null
}
```

Any `extra` fields you pass are merged into the JSON and **deep-redacted** for sensitive keys before serialization.

---

### `LogContext`

```python
class LogContext(
    *,
    job_id: str | None = None,
    request_id: str | None = None,
)
```

Context manager that injects `job_id` and/or `request_id` into every log record emitted within its scope. Uses Python's `contextvars` for thread-safe isolation.

```python
from dehelpers import get_logger, LogContext

log = get_logger("my_pipeline")

with LogContext(job_id="daily-sync", request_id="req-abc"):
    log.info("Processing")
    # JSON output includes "job_id": "daily-sync", "request_id": "req-abc"
```

Context values are automatically restored when the block exits.

---

## `dehelpers._redact` — Redaction Utilities

> **Note:** This is a private module (`_redact`). The functions below are used internally by the logger and API client. They are documented here because `redact_dict` is useful for extending redaction in custom code.

### `redact_dict`

```python
def redact_dict(
    d: dict,
    sensitive_keys: frozenset[str] | None = None,
    extra_sensitive_keys: frozenset[str] | None = None,
) → dict
```

Deep-clone a dictionary and replace values whose keys match the sensitive set with `"***REDACTED***"`.

Matching is **case-insensitive substring** — a key named `db_password` matches `password`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `d` | `dict` | — | Dictionary to redact (not mutated) |
| `sensitive_keys` | `frozenset[str] \| None` | `None` | Override the full sensitive-key set |
| `extra_sensitive_keys` | `frozenset[str] \| None` | `None` | Additional keys merged with the default set |

**Default sensitive keys:** `password`, `secret`, `token`, `api_key`, `authorization`, `dsn`, `connection_string`, `credential`, `passphrase`, `private_key`, `client_secret`.

```python
from dehelpers._redact import redact_dict

redact_dict({"db_password": "s3cret", "host": "localhost"})
# → {"db_password": "***REDACTED***", "host": "localhost"}
```

### `redact_url`

```python
def redact_url(
    url: str,
    sensitive_keys: frozenset[str] | None = None,
) → str
```

Return the URL with query-parameter values redacted for sensitive keys. Path segments are **not** redacted.

```python
from dehelpers._redact import redact_url

redact_url("https://api.example.com/data?api_key=abc123&page=1")
# → "https://api.example.com/data?api_key=***REDACTED***&page=1"
```

---

## `dehelpers.exceptions` — Exception Hierarchy

All exceptions inherit from `DPHError`, making it easy to catch any `dehelpers` error:

```python
from dehelpers import DPHError

try:
    ...
except DPHError as exc:
    logger.error("dehelpers error", exc_info=exc)
```

### Exception Tree

```
DPHError (base)
├── RetryError
├── PaginationError
└── DatabaseError
```

### `DPHError`

Base exception for all `dehelpers` errors.

### `RetryError`

Raised when all retry attempts are exhausted or `total_timeout` is exceeded.

| Attribute | Type | Description |
|---|---|---|
| `last_status` | `int \| None` | HTTP status code of the last attempt, or `None` for connection-level errors |
| `attempts` | `int` | Total number of attempts made |

The original exception is always preserved as `__cause__`.

### `PaginationError`

Raised on pagination failure.

| Attribute | Type | Description |
|---|---|---|
| `collected_items` | `list[dict]` | Items successfully fetched before the error |

This lets callers decide whether to use partial results:

```python
from dehelpers import PaginationError

try:
    items = list(client.paginate(url))
except PaginationError as exc:
    logger.warning(f"Partial: got {len(exc.collected_items)} items before failure")
    items = exc.collected_items
```

### `DatabaseError`

Raised on database operation failures. Wraps SQLAlchemy or driver-level exceptions while keeping the original available via `__cause__`.
