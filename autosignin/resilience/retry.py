"""
重试策略
提供指数退避+Jitter的重试机制
"""

import asyncio
import random
import time
from typing import Callable, Tuple, Type, Union
from functools import wraps

from autosignin.core.exceptions import (
    RetryableError,
    NonRetryableError,
    MaxRetriesExceededError
)


class RetryPolicy:
    """重试策略配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (RetryableError,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
    
    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(
        self,
        exception: Exception,
        attempt: int
    ) -> bool:
        """判断是否应该重试"""
        if attempt >= self.max_attempts:
            return False
        
        if isinstance(exception, NonRetryableError):
            return False
        
        return isinstance(exception, self.retryable_exceptions)


class RetryHandler:
    """重试处理器"""
    
    def __init__(self, policy: RetryPolicy = None):
        self.policy = policy or RetryPolicy()
        self.logger = None
    
    def set_logger(self, logger):
        self.logger = logger
    
    async def execute(self, func: Callable, *args, **kwargs):
        """执行带重试的函数调用"""
        last_exception = None
        
        for attempt in range(self.policy.max_attempts):
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 0 and self.logger:
                    self.logger.info(f"Retry succeeded on attempt {attempt + 1}")
                
                return result
                
            except NonRetryableError:
                raise
                
            except Exception as e:
                last_exception = e
                
                if self.policy.should_retry(e, attempt + 1):
                    delay = self.policy.calculate_delay(attempt)
                    
                    if self.logger:
                        self.logger.warning(
                            f"Attempt {attempt + 1}/{self.policy.max_attempts} "
                            f"failed: {e}. Retrying in {delay:.2f}s..."
                        )
                    
                    await asyncio.sleep(delay)
                else:
                    if self.logger:
                        self.logger.error(
                            f"Max retries ({self.policy.max_attempts}) exceeded: {e}"
                        )
                    raise MaxRetriesExceededError(
                        platform=getattr(e, 'platform', 'unknown'),
                        max_retries=self.policy.max_attempts
                    )
        
        raise last_exception


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """重试装饰器"""
    def decorator(func: Callable):
        policy = RetryPolicy(
            max_attempts=max_attempts,
            base_delay=base_delay,
            exponential_base=exponential_base,
            jitter=jitter
        )
        handler = RetryHandler(policy)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await handler.execute(func, *args, **kwargs)
        
        return wrapper
    return decorator


__all__ = ["RetryPolicy", "RetryHandler", "with_retry"]
