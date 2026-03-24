"""
平台基类
定义所有平台插件的接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from autosignin.models.signin import SignInResult
from autosignin.models.account import AccountHealth, AccountStatus


logger = logging.getLogger(__name__)


@dataclass
class PlatformMetadata:
    """平台元数据"""
    name: str
    display_name: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    homepage: str = ""
    max_retry: int = 3


@dataclass
class PlatformInstance:
    """平台实例"""
    metadata: PlatformMetadata
    cls: Type['BasePlatform']
    status: str = "discovered"
    error_message: str = ""
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.metadata.name,
            "display_name": self.metadata.display_name,
            "version": self.metadata.version,
            "status": self.status,
            "error_message": self.error_message,
            "last_used": (
                self.last_used.isoformat() 
                if self.last_used else None
            )
        }


class BasePlatform(ABC):
    """平台基类"""
    
    name: str = "unknown"
    display_name: str = "Unknown Platform"
    version: str = "1.0.0"
    metadata: PlatformMetadata = None
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        if self.metadata is None:
            self.metadata = PlatformMetadata(
                name=self.name,
                display_name=self.display_name,
                version=self.version
            )
    
    @abstractmethod
    async def sign_in(self, account_name: str, cookies: Dict[str, str]) -> SignInResult:
        """
        执行签到
        
        Args:
            account_name: 账号名称
            cookies: 登录凭证
            
        Returns:
            SignInResult: 签到结果
        """
        pass
    
    async def verify(self, cookies: Dict[str, str]) -> bool:
        """
        验证登录状态
        
        Args:
            cookies: 登录凭证
            
        Returns:
            bool: 是否有效
        """
        return True
    
    async def initialize(self) -> bool:
        """初始化平台"""
        self.logger.info(f"Initializing platform: {self.name}")
        return True
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info(f"Cleaning up platform: {self.name}")
    
    def validate_cookies(self, cookies: Dict[str, str]) -> tuple[bool, Optional[str]]:
        """
        验证 cookie 完整性
        
        Returns:
            (is_valid, error_message)
        """
        for field in self.metadata.required_fields:
            if field not in cookies or not cookies[field]:
                return False, f"Missing required field: {field}"
        return True, None
    
    async def health_check(self, cookies: Dict[str, str]) -> AccountHealth:
        """健康检查"""
        health = AccountHealth()
        health.last_check_at = datetime.now()
        
        try:
            is_valid, error = self.validate_cookies(cookies)
            if not is_valid:
                health.status = AccountStatus.AUTH_ERROR
                health.last_error_message = error
                health.last_error_at = datetime.now()
                return health
            
            if await self.verify(cookies):
                health.status = AccountStatus.NORMAL
                health.last_success_at = datetime.now()
            else:
                health.status = AccountStatus.AUTH_ERROR
                health.last_error_message = "Verification failed"
                health.last_error_at = datetime.now()
                
        except Exception as e:
            health.status = AccountStatus.AUTH_ERROR
            health.last_error_message = str(e)
            health.last_error_at = datetime.now()
        
        return health
    
    def get_stats(self) -> Dict[str, Any]:
        """获取平台统计"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "capabilities": self.metadata.capabilities
        }


def register_platform(
    name: str = None,
    display_name: str = None,
    version: str = "1.0.0",
    capabilities: List[str] = None,
    required_fields: List[str] = None
):
    """
    平台注册装饰器
    
    用法:
    
        @register_platform(
            name="bilibili",
            display_name="哔哩哔哩",
            version="1.2.0",
            capabilities=["daily_sign", "watch_video"],
            required_fields=["sessdata", "bili_jct"]
        )
        class BilibiliPlatform(BasePlatform):
            ...
    """
    def decorator(cls: Type[BasePlatform]) -> Type[BasePlatform]:
        cls.name = name or getattr(cls, 'name', None) or cls.__name__.lower()
        cls.display_name = display_name or getattr(cls, 'display_name', cls.name)
        cls.version = version
        
        cls.metadata = PlatformMetadata(
            name=cls.name,
            display_name=cls.display_name,
            version=version,
            capabilities=capabilities or [],
            required_fields=required_fields or []
        )
        
        return cls
    
    return decorator


__all__ = [
    "BasePlatform",
    "PlatformMetadata",
    "PlatformInstance",
    "register_platform",
]
