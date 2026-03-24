"""
自动恢复机制
根据故障类型自动执行恢复策略
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from autosignin.core.exceptions import (
    AuthError,
    RateLimitError,
    CircuitBreakerOpenError,
    NetworkError,
    TimeoutError,
    AccountBannedError
)


logger = logging.getLogger(__name__)


class FailureType(Enum):
    """故障类型"""
    NETWORK_ERROR = "network_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT = "rate_limit"
    CIRCUIT_BREAKER = "circuit_breaker"
    PLATFORM_ERROR = "platform_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class RecoveryStrategy:
    """恢复策略"""
    name: str
    action: str
    delay_seconds: int
    max_retries: int
    notification_required: bool


class AutoRecovery:
    """自动恢复机制"""

    DEFAULT_STRATEGIES = {
        FailureType.NETWORK_ERROR: RecoveryStrategy(
            name="network_error",
            action="retry_with_backoff",
            delay_seconds=5,
            max_retries=3,
            notification_required=False
        ),
        FailureType.AUTH_ERROR: RecoveryStrategy(
            name="auth_error",
            action="disable_account",
            delay_seconds=0,
            max_retries=0,
            notification_required=True
        ),
        FailureType.RATE_LIMIT: RecoveryStrategy(
            name="rate_limit",
            action="wait_and_retry",
            delay_seconds=60,
            max_retries=5,
            notification_required=False
        ),
        FailureType.CIRCUIT_BREAKER: RecoveryStrategy(
            name="circuit_breaker",
            action="wait_for_recovery",
            delay_seconds=60,
            max_retries=0,
            notification_required=True
        ),
        FailureType.PLATFORM_ERROR: RecoveryStrategy(
            name="platform_error",
            action="retry_with_backoff",
            delay_seconds=10,
            max_retries=3,
            notification_required=False
        ),
        FailureType.TIMEOUT: RecoveryStrategy(
            name="timeout",
            action="retry_with_timeout",
            delay_seconds=5,
            max_retries=2,
            notification_required=False
        ),
        FailureType.UNKNOWN: RecoveryStrategy(
            name="unknown",
            action="log_and_notify",
            delay_seconds=0,
            max_retries=0,
            notification_required=True
        )
    }

    def __init__(self, notifier=None, storage=None):
        self.notifier = notifier
        self.storage = storage
        self.strategies = self.DEFAULT_STRATEGIES.copy()
        self._disabled_accounts: Dict[str, Dict[str, Any]] = {}

    def classify_failure(self, error: Exception) -> FailureType:
        """分类故障类型"""
        if isinstance(error, AuthError):
            return FailureType.AUTH_ERROR
        elif isinstance(error, RateLimitError):
            return FailureType.RATE_LIMIT
        elif isinstance(error, CircuitBreakerOpenError):
            return FailureType.CIRCUIT_BREAKER
        elif isinstance(error, TimeoutError):
            return FailureType.TIMEOUT
        elif isinstance(error, NetworkError):
            return FailureType.NETWORK_ERROR
        elif isinstance(error, AccountBannedError):
            return FailureType.AUTH_ERROR
        else:
            return FailureType.UNKNOWN

    async def recover(
        self,
        failure_type: FailureType,
        context: Dict[str, Any],
        retry_func: Optional[Callable] = None
    ) -> bool:
        """执行恢复"""
        strategy = self.strategies.get(failure_type)

        if not strategy:
            logger.error(f"Unknown failure type: {failure_type}")
            return False

        logger.info(f"Starting recovery for {failure_type.value} with strategy {strategy.action}")

        if strategy.notification_required:
            await self._send_recovery_notification(failure_type, context, strategy)

        if strategy.action == "retry_with_backoff":
            return await self._retry_with_backoff(strategy, retry_func, context)
        elif strategy.action == "disable_account":
            return await self._disable_account(context)
        elif strategy.action == "wait_and_retry":
            return await self._wait_and_retry(strategy, retry_func, context)
        elif strategy.action == "wait_for_recovery":
            return await self._wait_for_recovery(strategy, context)
        elif strategy.action == "retry_with_timeout":
            return await self._retry_with_timeout(strategy, retry_func, context)
        elif strategy.action == "log_and_notify":
            await self._log_and_notify(failure_type, context)
            return False
        else:
            logger.warning(f"Unknown action: {strategy.action}")
            return False

    async def _retry_with_backoff(
        self,
        strategy: RecoveryStrategy,
        retry_func: Optional[Callable],
        context: Dict[str, Any]
    ) -> bool:
        """带退避的重试"""
        if not retry_func:
            return False

        platform = context.get("platform", "unknown")
        account = context.get("account", "unknown")

        for attempt in range(strategy.max_retries):
            delay = strategy.delay_seconds * (2 ** attempt)
            logger.info(f"Retry attempt {attempt + 1}/{strategy.max_retries} for {platform}/{account}, waiting {delay}s")

            await asyncio.sleep(delay)

            try:
                result = await retry_func()
                if result and getattr(result, "success", False):
                    logger.info(f"Recovery successful after {attempt + 1} attempts")
                    return True
            except Exception as e:
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                continue

        logger.error(f"Recovery failed after {strategy.max_retries} attempts")
        return False

    async def _disable_account(self, context: Dict[str, Any]) -> bool:
        """禁用账号"""
        platform = context.get("platform", "unknown")
        account = context.get("account", "unknown")
        reason = context.get("error", "Unknown")

        logger.warning(f"Disabling account {platform}/{account}: {reason}")

        self._disabled_accounts[f"{platform}/{account}"] = {
            "platform": platform,
            "account": account,
            "reason": reason,
            "disabled_at": asyncio.get_event_loop().time()
        }

        if self.storage:
            try:
                await self.storage.disable_account(platform, account)
            except Exception as e:
                logger.error(f"Failed to disable account in storage: {e}")

        return True

    async def _wait_and_retry(
        self,
        strategy: RecoveryStrategy,
        retry_func: Optional[Callable],
        context: Dict[str, Any]
    ) -> bool:
        """等待后重试"""
        if not retry_func:
            return False

        logger.info(f"Waiting {strategy.delay_seconds}s before retry...")
        await asyncio.sleep(strategy.delay_seconds)

        try:
            result = await retry_func()
            return result and getattr(result, "success", False)
        except Exception as e:
            logger.error(f"Wait and retry failed: {e}")
            return False

    async def _wait_for_recovery(
        self,
        strategy: RecoveryStrategy,
        context: Dict[str, Any]
    ) -> bool:
        """等待熔断恢复"""
        platform = context.get("platform", "unknown")
        logger.info(f"Waiting {strategy.delay_seconds}s for circuit breaker recovery for {platform}")

        await asyncio.sleep(strategy.delay_seconds)

        return True

    async def _retry_with_timeout(
        self,
        strategy: RecoveryStrategy,
        retry_func: Optional[Callable],
        context: Dict[str, Any]
    ) -> bool:
        """带超时重试"""
        if not retry_func:
            return False

        timeout = strategy.delay_seconds * 2

        try:
            result = await asyncio.wait_for(retry_func(), timeout=timeout)
            return result and getattr(result, "success", False)
        except asyncio.TimeoutError:
            logger.error(f"Retry timed out after {timeout}s")
            return False
        except Exception as e:
            logger.error(f"Retry with timeout failed: {e}")
            return False

    async def _send_recovery_notification(
        self,
        failure_type: FailureType,
        context: Dict[str, Any],
        strategy: RecoveryStrategy
    ):
        """发送恢复通知"""
        if not self.notifier:
            return

        platform = context.get("platform", "unknown")
        account = context.get("account", "unknown")
        error = context.get("error", str(failure_type.value))

        title = f"⚠️ {platform} 签到异常"
        content = f"平台: {platform}\n账号: {account}\n错误: {error}\n处理: {strategy.name}"

        try:
            await self.notifier.send(title, content)
        except Exception as e:
            logger.error(f"Failed to send recovery notification: {e}")

    async def _log_and_notify(
        self,
        failure_type: FailureType,
        context: Dict[str, Any]
    ):
        """记录并通知"""
        platform = context.get("platform", "unknown")
        account = context.get("account", "unknown")
        error = context.get("error", "Unknown error")

        logger.error(f"Unknown error for {platform}/{account}: {error}")

        if self.notifier:
            try:
                await self.notifier.send(
                    f"❌ {platform} 签到失败",
                    f"平台: {platform}\n账号: {account}\n错误: {error}"
                )
            except Exception as e:
                logger.error(f"Failed to send error notification: {e}")

    def is_account_disabled(self, platform: str, account: str) -> bool:
        """检查账号是否被禁用"""
        return f"{platform}/{account}" in self._disabled_accounts

    def get_disabled_accounts(self) -> Dict[str, Dict[str, Any]]:
        """获取被禁用的账号列表"""
        return self._disabled_accounts.copy()

    def reenable_account(self, platform: str, account: str) -> bool:
        """重新启用账号"""
        key = f"{platform}/{account}"
        if key in self._disabled_accounts:
            del self._disabled_accounts[key]
            logger.info(f"Re-enabled account {platform}/{account}")
            return True
        return False
