"""
限流器
基于 Token Bucket 算法的请求频率控制
"""

import asyncio
import time
from typing import Dict, Any, Optional

from autosignin.core.exceptions import RateLimitError


class RateLimiter:
    """基于 Token Bucket 的限流器"""
    
    def __init__(
        self,
        rate: float = 1.0,
        capacity: int = 10,
        platform: str = None
    ):
        self.rate = rate
        self.capacity = capacity
        self.platform = platform
        self._tokens = float(capacity)
        self._last_update = time.time()
        self._lock = asyncio.Lock()
        
        self._total_requests = 0
        self._rejected_requests = 0
    
    async def acquire(self, tokens: int = 1, timeout: float = None) -> bool:
        """
        获取 token
        
        Args:
            tokens: 需要获取的 token 数量
            timeout: 等待超时(秒)
            
        Returns:
            bool: 是否成功获取
        """
        start_time = time.time()
        
        while True:
            async with self._lock:
                self._replenish()
                
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    self._total_requests += 1
                    return True
                
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        self._rejected_requests += 1
                        return False
            
            await asyncio.sleep(0.1)
    
    def _replenish(self):
        """补充 token"""
        now = time.time()
        elapsed = now - self._last_update
        
        new_tokens = elapsed * self.rate
        self._tokens = min(self.capacity, self._tokens + new_tokens)
        self._last_update = now
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "tokens": self._tokens,
            "capacity": self.capacity,
            "rate": self.rate,
            "total_requests": self._total_requests,
            "rejected_requests": self._rejected_requests,
            "rejection_rate": (
                self._rejected_requests / self._total_requests 
                if self._total_requests > 0 else 0
            )
        }


class RateLimitMiddleware:
    """限流中间件"""
    
    def __init__(
        self,
        default_rate: float = 1.0,
        default_capacity: int = 10
    ):
        self._limiters: Dict[str, RateLimiter] = {}
        self._default_rate = default_rate
        self._default_capacity = default_capacity
    
    def configure(
        self,
        platform: str,
        rate: float = None,
        capacity: int = None
    ):
        """配置平台的限流参数"""
        self._limiters[platform] = RateLimiter(
            rate=rate or self._default_rate,
            capacity=capacity or self._default_capacity,
            platform=platform
        )
    
    def get_limiter(self, platform: str) -> RateLimiter:
        """获取或创建限流器"""
        if platform not in self._limiters:
            self._limiters[platform] = RateLimiter(
                rate=self._default_rate,
                capacity=self._default_capacity,
                platform=platform
            )
        return self._limiters[platform]
    
    async def check_and_execute(
        self,
        platform: str,
        func,
        *args,
        **kwargs
    ):
        """检查限流并执行函数"""
        limiter = self.get_limiter(platform)
        
        if not await limiter.acquire(timeout=5.0):
            raise RateLimitError(
                platform=platform,
                retry_after=int(
                    (limiter.capacity - limiter._tokens) / limiter.rate
                )
            )
        
        return await func(*args, **kwargs)


__all__ = ["RateLimiter", "RateLimitMiddleware"]
