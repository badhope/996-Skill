"""
异常类体系
定义签到系统可能出现的各类异常
"""

from typing import Optional, Any
from datetime import datetime


class SignInException(Exception):
    """签到基础异常"""
    
    def __init__(
        self,
        message: str,
        code: int = 5000,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class RetryableError(SignInException):
    """可重试错误 - 网络抖动、临时故障等"""
    
    def __init__(self, message: str, code: int = 5100, **kwargs):
        super().__init__(message, code, kwargs)


class NonRetryableError(SignInException):
    """不可重试错误 - 配置错误、认证失败等"""
    
    def __init__(self, message: str, code: int = 5200, **kwargs):
        super().__init__(message, code, kwargs)


class NetworkError(RetryableError):
    """网络连接失败"""
    
    def __init__(
        self,
        message: str = "Network connection failed",
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message, code=5101)
        self.original_exception = original_exception


class TimeoutError(RetryableError):
    """请求超时"""
    
    def __init__(self, timeout_seconds: float):
        super().__init__(f"Request timeout after {timeout_seconds}s", code=5102)
        self.timeout_seconds = timeout_seconds


class RateLimitError(RetryableError):
    """触发限流"""
    
    def __init__(
        self,
        platform: str,
        retry_after: Optional[int] = None
    ):
        super().__init__(
            f"Rate limit exceeded for {platform}",
            code=5103
        )
        self.platform = platform
        self.retry_after = retry_after


class ServiceUnavailableError(RetryableError):
    """服务不可用"""
    
    def __init__(self, platform: str, reason: Optional[str] = None):
        msg = f"Platform {platform} is unavailable"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code=5104)
        self.platform = platform


class AuthError(NonRetryableError):
    """认证失败/过期"""
    
    def __init__(self, platform: str, reason: str = "Token expired"):
        super().__init__(
            f"Authentication failed for {platform}: {reason}",
            code=5201
        )
        self.platform = platform
        self.reason = reason


class AccountBannedError(NonRetryableError):
    """账号被封禁"""
    
    def __init__(
        self,
        platform: str,
        account: str,
        until: Optional[datetime] = None
    ):
        msg = f"Account {account} is banned on {platform}"
        if until:
            msg += f" until {until}"
        super().__init__(msg, code=5202)
        self.platform = platform
        self.account = account
        self.until = until


class ConfigError(NonRetryableError):
    """配置错误"""
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Config error in {field}: {reason}",
            code=5203
        )
        self.field = field


class ValidationError(NonRetryableError):
    """数据校验失败"""
    
    def __init__(
        self,
        field: str,
        value: Any,
        constraint: str
    ):
        super().__init__(
            f"Validation failed for {field}={value}: {constraint}",
            code=5204
        )


class PlatformNotSupportedError(NonRetryableError):
    """平台不支持"""
    
    def __init__(self, platform: str):
        super().__init__(
            f"Platform not supported: {platform}",
            code=5205
        )
        self.platform = platform


class CircuitBreakerOpenError(RetryableError):
    """熔断器打开"""
    
    def __init__(self, platform: str, message: Optional[str] = None):
        msg = message or f"Circuit breaker is OPEN for {platform}"
        super().__init__(msg, code=5105)
        self.platform = platform


class MaxRetriesExceededError(NonRetryableError):
    """超过最大重试次数"""
    
    def __init__(self, platform: str, max_retries: int):
        super().__init__(
            f"Max retries ({max_retries}) exceeded for {platform}",
            code=5206
        )
        self.platform = platform
        self.max_retries = max_retries


class BulkheadFullError(NonRetryableError):
    """舱壁已满"""
    
    def __init__(self, platform: str, max_concurrent: int):
        super().__init__(
            f"Bulkhead is full for {platform}: max concurrent = {max_concurrent}",
            code=5207
        )
        self.platform = platform
        self.max_concurrent = max_concurrent


__all__ = [
    "SignInException",
    "RetryableError",
    "NonRetryableError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
    "AuthError",
    "AccountBannedError",
    "ConfigError",
    "ValidationError",
    "PlatformNotSupportedError",
    "CircuitBreakerOpenError",
    "MaxRetriesExceededError",
    "BulkheadFullError",
]
