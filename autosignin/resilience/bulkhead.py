"""
舱壁隔离
限制并发执行数，防止某个平台占用全部资源
"""

import asyncio
from typing import Dict, Any, Callable

from autosignin.core.exceptions import BulkheadFullError


class Bulkhead:
    """舱壁模式实现"""
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 0,
        name: str = "default"
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.name = name
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0
        self._queue_size = 0
        self._lock = asyncio.Lock()
        
        self._total_executions = 0
        self._rejected_executions = 0
    
    async def execute(self, func: Callable, *args, **kwargs):
        """通过舱壁执行函数"""
        async with self._lock:
            if self._active_count >= self.max_concurrent:
                if self.max_queue_size == 0 or self._queue_size >= self.max_queue_size:
                    self._rejected_executions += 1
                    raise BulkheadFullError(
                        platform=self.name,
                        max_concurrent=self.max_concurrent
                    )
                self._queue_size += 1
        
        try:
            async with self._semaphore:
                async with self._lock:
                    self._active_count += 1
                    self._queue_size = max(0, self._queue_size - 1)
                
                try:
                    return await func(*args, **kwargs)
                finally:
                    async with self._lock:
                        self._active_count -= 1
                    self._total_executions += 1
                    
        except Exception as e:
            self._rejected_executions += 1
            raise
    
    @property
    def available_capacity(self) -> int:
        return self.max_concurrent - self._active_count
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "active": self._active_count,
            "max": self.max_concurrent,
            "queue": self._queue_size,
            "queue_max": self.max_queue_size,
            "total_executions": self._total_executions,
            "rejected_executions": self._rejected_executions
        }


class BulkheadRegistry:
    """舱壁注册表"""
    
    def __init__(self):
        self._bulkheads: Dict[str, Bulkhead] = {}
        self._lock = asyncio.Lock()
    
    def get_or_create(
        self,
        platform: str,
        max_concurrent: int = 5,
        max_queue: int = 0
    ) -> Bulkhead:
        """获取或创建舱壁"""
        if platform not in self._bulkheads:
            self._bulkheads[platform] = Bulkhead(
                max_concurrent=max_concurrent,
                max_queue_size=max_queue,
                name=platform
            )
        return self._bulkheads[platform]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有舱壁状态"""
        return {name: bh.stats for name, bh in self._bulkheads.items()}


__all__ = ["Bulkhead", "BulkheadRegistry"]
