"""dehelpers: Lightweight utilities for data engineering pipelines."""

from dehelpers.api import NextLinkPagination, ResilientClient, RetryPolicy
from dehelpers.db import DatabaseManager
from dehelpers.exceptions import (
    DatabaseError,
    DPHError,
    PaginationError,
    RetryError,
)
from dehelpers.logger import LogContext, get_logger

__all__ = [
    # API
    "ResilientClient",
    "RetryPolicy",
    "NextLinkPagination",
    # Database
    "DatabaseManager",
    # Logger
    "get_logger",
    "LogContext",
    # Exceptions
    "DPHError",
    "RetryError",
    "PaginationError",
    "DatabaseError",
]

__version__ = "0.1.0"
