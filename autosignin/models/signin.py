"""
签到相关数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SignInResult:
    """签到结果"""
    request_id: str = ""
    platform: str = ""
    account: str = ""
    success: bool = False
    status_code: Optional[int] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    error_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "platform": self.platform,
            "account": self.account,
            "success": self.success,
            "status_code": self.status_code,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "error_type": self.error_type
        }


@dataclass
class SignInRequest:
    """签到请求"""
    request_id: str = ""
    platforms: List[str] = field(default_factory=list)
    accounts: List[str] = field(default_factory=list)
    force: bool = False
    dry_run: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SignInTask:
    """签到任务"""
    task_id: str
    request: SignInRequest
    results: List[SignInResult] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def failure_count(self) -> int:
        return len(self.results) - self.success_count


@dataclass
class SignInRecord:
    """签到记录（持久化用）"""
    id: Optional[int] = None
    request_id: str = ""
    platform: str = ""
    account: str = ""
    success: bool = False
    status_code: Optional[int] = None
    message: str = ""
    error_type: Optional[str] = None
    duration_ms: int = 0
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "request_id": self.request_id,
            "platform": self.platform,
            "account": self.account,
            "success": self.success,
            "status_code": self.status_code,
            "message": self.message,
            "error_type": self.error_type,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "metadata": self.metadata
        }


__all__ = [
    "TaskStatus",
    "SignInResult",
    "SignInRequest",
    "SignInTask",
    "SignInRecord",
]
