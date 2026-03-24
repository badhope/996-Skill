"""
熔断器
防止级联故障的三状态机实现
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Dict, Any, Optional

from autosignin.core.exceptions import CircuitBreakerOpenError


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.name = name
        
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitBreakerState:
        return self._state
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time
        }
    
    async def call(self, func: Callable, *args, **kwargs):
        """通过熔断器执行函数"""
        await self._check_and_transition_state()
        
        async with self._lock:
            if self._state == CircuitBreakerState.OPEN:
                raise CircuitBreakerOpenError(
                    platform=self.name,
                    message=f"Circuit breaker '{self.name}' is OPEN. "
                            f"Wait {self._get_recovery_wait_time():.0f}s before retry."
                )
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        platform=self.name,
                        message=f"Circuit breaker '{self.name}' is HALF_OPEN "
                                f"and max calls ({self.half_open_max_calls}) reached"
                    )
                self._half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _check_and_transition_state(self):
        """检查并处理状态转换"""
        async with self._lock:
            if self._state == CircuitBreakerState.OPEN:
                if self._last_failure_time is not None:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.recovery_timeout:
                        self._transition_to_half_open()
    
    def _transition_to_half_open(self):
        """转换到 HALF_OPEN 状态"""
        import logging
        logging.getLogger(__name__).info(
            f"Circuit breaker '{self.name}' transitioning: OPEN → HALF_OPEN"
        )
        self._state = CircuitBreakerState.HALF_OPEN
        self._half_open_calls = 0
        self._success_count = 0
    
    async def _on_success(self):
        """处理成功调用"""
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                
                if self._success_count >= self.half_open_max_calls:
                    import logging
                    logging.getLogger(__name__).info(
                        f"Circuit breaker '{self.name}' transitioning: "
                        f"HALF_OPEN → CLOSED (success: {self._success_count})"
                    )
                    self._reset()
            else:
                self._failure_count = 0
    
    async def _on_failure(self):
        """处理失败调用"""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            import logging
            logger = logging.getLogger(__name__)
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}' transitioning: "
                    f"HALF_OPEN → OPEN (failure in half-open)"
                )
                self._state = CircuitBreakerState.OPEN
                
            elif self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker '{self.name}' transitioning: "
                    f"CLOSED → OPEN (failures: {self._failure_count})"
                )
                self._state = CircuitBreakerState.OPEN
    
    def _reset(self):
        """重置熔断器到关闭状态"""
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
    
    def _get_recovery_wait_time(self) -> float:
        """获取距离恢复尝试的等待时间"""
        if self._last_failure_time is None:
            return 0
        elapsed = time.time() - self._last_failure_time
        return max(0, self.recovery_timeout - elapsed)


class CircuitBreakerRegistry:
    """熔断器注册表"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    def get(
        self,
        name: str,
        **kwargs
    ) -> CircuitBreaker:
        """获取或创建熔断器"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器状态"""
        return {name: cb.stats for name, cb in self._breakers.items()}


__all__ = ["CircuitBreaker", "CircuitBreakerState", "CircuitBreakerRegistry"]
