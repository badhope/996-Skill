"""
任务调度器
基于 APScheduler 的定时任务管理
"""

import asyncio
import logging
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)


logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={
                "coalesce": False,
                "max_instances": 3,
                "misfire_grace_time": 300
            }
        )
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def add_listener(self):
        """添加调度器事件监听器"""
        def on_job_executed(event):
            if event.exception:
                logger.error(f"Job {event.job_id} executed with error: {event.exception}")
            else:
                logger.info(f"Job {event.job_id} executed successfully")
        
        def on_job_error(event):
            logger.error(f"Job {event.job_id} error: {event.exception}")
        
        def on_job_missed(event):
            logger.warning(f"Job {event.job_id} missed")
        
        self._scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
        self._scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)
        self._scheduler.add_listener(on_job_missed, EVENT_JOB_MISSED)
    
    def register_handler(self, name: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[name] = handler
        logger.info(f"Task handler registered: {name}")
    
    def add_cron_job(
        self,
        job_id: str,
        handler_name: str,
        cron_expression: str,
        timezone: str = "Asia/Shanghai",
        **kwargs
    ):
        """添加 Cron 任务"""
        if handler_name not in self._handlers:
            raise ValueError(f"Handler not found: {handler_name}")
        
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone=timezone
        )
        
        self._scheduler.add_job(
            func=self._handlers[handler_name],
            trigger=trigger,
            id=job_id,
            name=kwargs.get("name", job_id),
            replace_existing=True,
            **kwargs
        )
        
        self._tasks[job_id] = {
            "type": "cron",
            "handler": handler_name,
            "expression": cron_expression,
            "timezone": timezone,
            "next_run": None
        }
        
        logger.info(f"Cron job added: {job_id} = {cron_expression}")
    
    def add_interval_job(
        self,
        job_id: str,
        handler_name: str,
        seconds: int = None,
        minutes: int = None,
        hours: int = None,
        **kwargs
    ):
        """添加间隔任务"""
        if handler_name not in self._handlers:
            raise ValueError(f"Handler not found: {handler_name}")
        
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            **kwargs
        )
        
        self._scheduler.add_job(
            func=self._handlers[handler_name],
            trigger=trigger,
            id=job_id,
            name=kwargs.get("name", job_id),
            replace_existing=True,
            **kwargs
        )
        
        self._tasks[job_id] = {
            "type": "interval",
            "handler": handler_name,
            "next_run": None
        }
        
        logger.info(f"Interval job added: {job_id}")
    
    def add_one_shot_job(
        self,
        job_id: str,
        handler_name: str,
        run_date: datetime,
        **kwargs
    ):
        """添加一次性任务"""
        if handler_name not in self._handlers:
            raise ValueError(f"Handler not found: {handler_name}")
        
        trigger = DateTrigger(run_date=run_date)
        
        self._scheduler.add_job(
            func=self._handlers[handler_name],
            trigger=trigger,
            id=job_id,
            name=kwargs.get("name", job_id),
            replace_existing=True,
            **kwargs
        )
        
        self._tasks[job_id] = {
            "type": "oneshot",
            "handler": handler_name,
            "run_date": run_date.isoformat()
        }
        
        logger.info(f"One-shot job added: {job_id} at {run_date}")
    
    def remove_job(self, job_id: str):
        """移除任务"""
        self._scheduler.remove_job(job_id)
        if job_id in self._tasks:
            del self._tasks[job_id]
        logger.info(f"Job removed: {job_id}")
    
    def pause_job(self, job_id: str):
        """暂停任务"""
        self._scheduler.pause_job(job_id)
        logger.info(f"Job paused: {job_id}")
    
    def resume_job(self, job_id: str):
        """恢复任务"""
        self._scheduler.resume_job(job_id)
        logger.info(f"Job resumed: {job_id}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        job = self._scheduler.get_job(job_id)
        if job is None:
            return None
        
        task_info = self._tasks.get(job_id, {})
        
        return {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            **task_info
        }
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        jobs = self._scheduler.get_jobs()
        return [self.get_job(job.id) for job in jobs if job.id]
    
    def start(self):
        """启动调度器"""
        self.add_listener()
        self._scheduler.start()
        logger.info("Task scheduler started")
    
    def shutdown(self, wait: bool = True):
        """关闭调度器"""
        self._scheduler.shutdown(wait=wait)
        logger.info("Task scheduler shutdown")
    
    def run_job_now(self, job_id: str):
        """立即运行任务"""
        job = self._scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Job triggered to run now: {job_id}")
        else:
            logger.warning(f"Job not found: {job_id}")
    
    @property
    def running(self) -> bool:
        """检查调度器是否运行"""
        return self._scheduler.running


__all__ = ["TaskScheduler"]
