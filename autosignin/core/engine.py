"""
签到引擎
核心业务逻辑，负责协调各模块
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any

from autosignin.core.exceptions import (
    SignInException,
    AuthError,
    RateLimitError,
    CircuitBreakerOpenError,
    BulkheadFullError,
    NonRetryableError
)
from autosignin.core.notifier import NotificationManager
from autosignin.core.storage import StorageAdapter
from autosignin.core.scheduler import TaskScheduler
from autosignin.platforms.base import BasePlatform
from autosignin.platforms.manager import PlatformManager
from autosignin.resilience.retry import RetryPolicy, RetryHandler
from autosignin.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from autosignin.resilience.rate_limiter import RateLimiter, RateLimitMiddleware
from autosignin.resilience.bulkhead import Bulkhead, BulkheadRegistry
from autosignin.models.signin import SignInRequest, SignInResult, SignInTask, TaskStatus, SignInRecord


logger = logging.getLogger(__name__)


class SignInEngine:
    """签到引擎"""
    
    def __init__(
        self,
        platform_manager: PlatformManager,
        storage: StorageAdapter,
        notifier: NotificationManager,
        scheduler: TaskScheduler = None,
        max_concurrent: int = 5,
        default_retry_policy: RetryPolicy = None,
        default_rate_limit: float = 1.0,
        default_rate_capacity: int = 10
    ):
        self.platform_manager = platform_manager
        self.storage = storage
        self.notifier = notifier
        self.scheduler = scheduler
        
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        self.retry_handler = RetryHandler(
            default_retry_policy or RetryPolicy()
        )
        self.retry_handler.set_logger(logger)
        
        self.circuit_breakers = CircuitBreakerRegistry()
        self.rate_limiter = RateLimitMiddleware(
            default_rate=default_rate_limit,
            default_capacity=default_rate_capacity
        )
        self.bulkheads = BulkheadRegistry()
        
        self._tasks: Dict[str, SignInTask] = {}
    
    async def execute_sign_in(
        self,
        platform: BasePlatform,
        account_name: str,
        cookies: Dict[str, str],
        force: bool = False
    ) -> SignInResult:
        """执行单个签到任务"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        retry_count = 0
        
        result = SignInResult(
            request_id=request_id,
            platform=platform.name,
            account=account_name
        )
        
        try:
            is_valid, error_msg = platform.validate_cookies(cookies)
            if not is_valid:
                raise AuthError(platform=platform.name, reason=error_msg)
            
            if not force:
                is_signed = await self.storage.async_is_already_signed_today(
                    platform=platform.name,
                    account=account_name
                )
                if is_signed:
                    result.success = True
                    result.message = "Already signed today"
                    result.duration_ms = int((time.time() - start_time) * 1000)
                    return result
            
            circuit_breaker = self.circuit_breakers.get(
                platform.name,
                failure_threshold=5,
                recovery_timeout=60
            )
            
            bulkhead = self.bulkheads.get_or_create(
                platform.name,
                max_concurrent=3
            )
            
            async def sign_in_with_protection():
                nonlocal retry_count
                
                async def do_sign_in():
                    nonlocal retry_count
                    return await platform.sign_in(account_name, cookies)
                
                try:
                    sign_result = await circuit_breaker.call(do_sign_in)
                    retry_count = getattr(do_sign_in, '_retry_count', 0)
                    return sign_result
                except CircuitBreakerOpenError:
                    raise
                except BulkheadFullError:
                    raise
            
            sign_result = await bulkhead.execute(sign_in_with_protection)
            
            result.success = sign_result.success
            result.status_code = sign_result.get("status_code")
            result.message = sign_result.get("message", "")
            result.data = sign_result
            
        except AuthError as e:
            result.success = False
            result.error = str(e)
            result.error_type = "AuthError"
            logger.error(f"Auth error for {platform.name}/{account_name}: {e}")
            
        except RateLimitError as e:
            result.success = False
            result.error = f"Rate limited: {e}"
            result.error_type = "RateLimitError"
            logger.warning(f"Rate limit for {platform.name}/{account_name}")
            
        except CircuitBreakerOpenError as e:
            result.success = False
            result.error = f"Circuit breaker open: {e}"
            result.error_type = "CircuitBreakerOpen"
            logger.warning(f"Circuit breaker open for {platform.name}")
            
        except BulkheadFullError as e:
            result.success = False
            result.error = f"Bulkhead full: {e}"
            result.error_type = "BulkheadFull"
            logger.warning(f"Bulkhead full for {platform.name}")
            
        except NonRetryableError as e:
            result.success = False
            result.error = str(e)
            result.error_type = type(e).__name__
            logger.error(f"Non-retryable error for {platform.name}/{account_name}: {e}")
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            result.error_type = "UnknownError"
            logger.exception(f"Unexpected error for {platform.name}/{account_name}")
        
        finally:
            result.duration_ms = int((time.time() - start_time) * 1000)
            result.retry_count = retry_count
            result.timestamp = asyncio.get_event_loop().time
            
            record = SignInRecord(
                request_id=request_id,
                platform=platform.name,
                account=account_name,
                success=result.success,
                status_code=result.status_code,
                message=result.message,
                error_type=result.error_type,
                duration_ms=result.duration_ms,
                retry_count=result.retry_count
            )
            
            await self.storage.async_save_sign_in_result(record)
        
        return result
    
    async def execute_sign_in_batch(
        self,
        request: SignInRequest
    ) -> SignInTask:
        """批量执行签到"""
        task_id = str(uuid.uuid4())
        task = SignInTask(
            task_id=task_id,
            request=request,
            status=TaskStatus.RUNNING,
            started_at=asyncio.get_event_loop().time
        )
        
        self._tasks[task_id] = task
        
        try:
            platforms_to_sign = []
            
            for platform_name in request.platforms:
                platform = await self.platform_manager.get_platform(platform_name)
                if not platform:
                    logger.warning(f"Platform not found: {platform_name}")
                    continue
                
                account_names = request.accounts or [a["name"] for a in getattr(platform, 'accounts', [])]
                
                for account_name in account_names:
                    cookies = self._get_cookies_for_account(platform.name, account_name)
                    if not cookies:
                        logger.warning(f"No cookies for {platform.name}/{account_name}")
                        continue
                    
                    platforms_to_sign.append((platform, account_name, cookies))
            
            async def sign_with_semaphore(platform, account_name, cookies):
                async with self._semaphore:
                    return await self.execute_sign_in(
                        platform, account_name, cookies, request.force
                    )
            
            results = await asyncio.gather(
                *[sign_with_semaphore(p, a, c) for p, a, c in platforms_to_sign],
                return_exceptions=True
            )
            
            for r in results:
                if isinstance(r, Exception):
                    logger.error(f"Sign-in task exception: {r}")
                    task.results.append(SignInResult(
                        request_id=task_id,
                        success=False,
                        error=str(r)
                    ))
                else:
                    task.results.append(r)
            
            if task.failure_count > 0 and task.success_count > 0:
                task.status = TaskStatus.PARTIAL_SUCCESS
            elif task.failure_count == 0:
                task.status = TaskStatus.SUCCESS
            else:
                task.status = TaskStatus.FAILED
                
        except Exception as e:
            logger.exception(f"Batch sign-in error: {e}")
            task.status = TaskStatus.FAILED
        
        finally:
            task.completed_at = asyncio.get_event_loop().time
        
        return task
    
    def _get_cookies_for_account(
        self,
        platform: str,
        account_name: str
    ) -> Optional[Dict[str, str]]:
        """获取账号 Cookie"""
        from autosignin.config.models import AccountsConfig
        
        if hasattr(self, '_config'):
            accounts: AccountsConfig = self._config.accounts
            
            if platform == "bilibili" and accounts.bilibili:
                for acc in accounts.bilibili:
                    if acc.name == account_name:
                        return {
                            "sessdata": acc.sessdata,
                            "bili_jct": acc.bili_jct,
                            "buvid3": acc.buvid3
                        }
            
            elif platform == "netease_music" and accounts.netease_music:
                for acc in accounts.netease_music:
                    if acc.name == account_name:
                        return {"cookie": acc.cookie}
        
        return None
    
    def set_config(self, config):
        """设置配置"""
        self._config = config
    
    def get_task(self, task_id: str) -> Optional[SignInTask]:
        """获取任务状态"""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[SignInTask]:
        """获取所有任务"""
        return list(self._tasks.values())
    
    async def cleanup_completed_tasks(self, max_age_seconds: int = 3600):
        """清理已完成的任务"""
        now = asyncio.get_event_loop().time()
        to_remove = []

        for task_id, task in self._tasks.items():
            if task.completed_at and (now - task.completed_at) > max_age_seconds:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        return len(to_remove)

    async def graceful_shutdown(self, timeout_seconds: int = 30):
        """优雅关闭

        Args:
            timeout_seconds: 等待任务完成的最大超时时间

        Returns:
            bool: 是否成功关闭
        """
        logger.info(f"Starting graceful shutdown (timeout: {timeout_seconds}s)...")

        running_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
        if running_tasks:
            logger.info(f"Waiting for {len(running_tasks)} running tasks to complete...")

            try:
                await asyncio.wait_for(
                    asyncio.gather(*[self._wait_for_task(t.task_id) for t in running_tasks]),
                    timeout=timeout_seconds
                )
                logger.info("All running tasks completed")
            except asyncio.TimeoutError:
                logger.warning(f"Shutdown timeout, {len(running_tasks)} tasks still running")
                for task in running_tasks:
                    task.status = TaskStatus.FAILED
                    task.message = "Shutdown timeout"

        if self.scheduler:
            logger.info("Stopping scheduler...")
            self.scheduler.shutdown(wait=True)

        if self.storage:
            logger.info("Closing storage...")
            self.storage.close()

        logger.info("Graceful shutdown completed")
        return True

    async def _wait_for_task(self, task_id: str, poll_interval: float = 0.5):
        """等待任务完成"""
        while True:
            task = self._tasks.get(task_id)
            if not task or task.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.PARTIAL_SUCCESS):
                break
            await asyncio.sleep(poll_interval)


__all__ = ["SignInEngine"]
