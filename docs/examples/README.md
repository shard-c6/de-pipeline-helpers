# Examples

Runnable example scripts demonstrating `dehelpers` in action. Each script is self-contained and can be copied and executed directly.

| Script | Description |
|---|---|
| [basic_http_client.py](basic_http_client.py) | Simple GET request with default and custom retry policies |
| [paginated_ingestion.py](paginated_ingestion.py) | Complete API → PostgreSQL pipeline with pagination, logging, and error handling |
| [structured_logging.py](structured_logging.py) | Logger setup, `LogContext` scoping, and secret redaction demonstration |

## Running the Examples

```bash
# Install dehelpers first
pip install dehelpers[dataframe]

# Run any example
python docs/examples/basic_http_client.py
python docs/examples/structured_logging.py

# The paginated ingestion example requires DATABASE_URL
DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/mydb" \
    python docs/examples/paginated_ingestion.py
```
