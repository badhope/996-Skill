"""
任务调度器 - 基于 schedule 的定时任务
"""

import asyncio
import threading
from typing import Dict, Any, Callable
from datetime import datetime

import schedule
from loguru import logger


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cron = config.get("cron", "0 9 * * *")
        self.running = False
        self._thread = None
        self._loop = None
    
    def add_job(self, func: Callable, *args, **kwargs):
        """添加定时任务"""
        # 解析 cron 表达式
        parts = self.cron.split()
        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            
            job = schedule.every()
            
            # 设置分钟
            if minute != "*":
                job = job.at(f"{int(hour):02d}:{int(minute):02d}")
            
            # 设置小时
            if hour != "*" and minute == "*":
                job = job.hour
            
            logger.info(f"定时任务已设置: {self.cron}")
            
            # 包装异步函数
            def wrapper():
                asyncio.run_coroutine_threadsafe(func(), self._loop)
            
            job.do(wrapper)
    
    def _run(self):
        """运行调度循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        while self.running:
            schedule.run_pending()
            asyncio.sleep(1)
    
    def start(self):
        """启动调度器"""
        self.running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
        logger.info("调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self._thread:
            self._thread.join()
        logger.info("调度器已停止")
