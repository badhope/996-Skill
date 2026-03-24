"""
Auto-SignIn - 多平台自动签到系统
"""

__version__ = "2.0.0"
__author__ = "Auto-SignIn Team"

from autosignin.core.engine import SignInEngine
from autosignin.core.notifier import NotificationManager
from autosignin.core.scheduler import TaskScheduler
from autosignin.core.storage import StorageAdapter, SQLiteStorageAdapter
from autosignin.core.exceptions import *
from autosignin.config import ConfigManager

__all__ = [
    "SignInEngine",
    "NotificationManager",
    "TaskScheduler",
    "StorageAdapter",
    "SQLiteStorageAdapter",
    "ConfigManager",
]
