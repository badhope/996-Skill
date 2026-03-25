"""核心模块"""

from autosignin.core.engine import SignInEngine
from autosignin.core.notifier import NotificationManager
from autosignin.core.scheduler import TaskScheduler
from autosignin.core.storage import StorageAdapter, SQLiteStorageAdapter
from autosignin.core.exceptions import (
    SignInException,
    AuthError,
    RateLimitError,
    NetworkError,
    TimeoutError
)

__all__ = [
    "SignInEngine",
    "NotificationManager",
    "TaskScheduler",
    "StorageAdapter",
    "SQLiteStorageAdapter",
    "SignInException",
    "AuthError",
    "RateLimitError",
    "NetworkError",
    "TimeoutError",
]
