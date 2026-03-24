"""
账号相关数据模型
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AccountStatus(Enum):
    NORMAL = "normal"
    AUTH_ERROR = "auth_error"
    RATE_LIMITED = "rate_limited"
    BANNED = "banned"
    DISABLED = "disabled"


@dataclass
class AccountHealth:
    """账号健康状态"""
    status: AccountStatus = AccountStatus.NORMAL
    consecutive_failures: int = 0
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: str = ""
    last_check_at: Optional[datetime] = None
    total_sign_ins: int = 0
    successful_sign_ins: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_sign_ins == 0:
            return 0.0
        return self.successful_sign_ins / self.total_sign_ins
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "consecutive_failures": self.consecutive_failures,
            "last_success_at": (
                self.last_success_at.isoformat() 
                if self.last_success_at else None
            ),
            "last_error_at": (
                self.last_error_at.isoformat() 
                if self.last_error_at else None
            ),
            "last_error_message": self.last_error_message,
            "last_check_at": (
                self.last_check_at.isoformat() 
                if self.last_check_at else None
            ),
            "total_sign_ins": self.total_sign_ins,
            "successful_sign_ins": self.successful_sign_ins,
            "success_rate": self.success_rate
        }


@dataclass
class Account:
    """账号"""
    id: Optional[int] = None
    platform: str = ""
    name: str = ""
    cookie: str = ""
    status: AccountStatus = AccountStatus.NORMAL
    health: AccountHealth = field(default_factory=AccountHealth)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "platform": self.platform,
            "name": self.name,
            "cookie": self.cookie,
            "status": self.status.value,
            "health": self.health.to_dict(),
            "created_at": (
                self.created_at.isoformat() 
                if isinstance(self.created_at, datetime) else self.created_at
            ),
            "updated_at": (
                self.updated_at.isoformat() 
                if isinstance(self.updated_at, datetime) else self.updated_at
            ),
            "extra": self.extra
        }


__all__ = ["AccountStatus", "AccountHealth", "Account"]
