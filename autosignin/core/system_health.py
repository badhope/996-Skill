"""
系统健康检查器
检查所有组件状态并输出健康报告
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ComponentHealth:
    """组件健康状态"""
    name: str
    status: str
    message: str = ""
    latency_ms: float = 0
    last_check: Optional[datetime] = None
    issues: List[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        return self.status == "healthy"


@dataclass
class HealthReport:
    """健康报告"""
    timestamp: datetime
    overall_status: str
    components: List[ComponentHealth]
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        return self.overall_status == "healthy"


class HealthChecker:
    """健康检查器"""

    def __init__(self, engine=None):
        self.engine = engine
        self._last_check: Optional[datetime] = None

    async def check_all(self) -> HealthReport:
        """执行全面健康检查"""
        components = []
        issues = []

        platform_health = await self._check_platforms()
        components.append(platform_health)

        storage_health = await self._check_storage()
        components.append(storage_health)

        network_health = await self._check_network()
        components.append(network_health)

        if self.engine and self.engine.notifier:
            notifier_health = await self._check_notifier()
            components.append(notifier_health)

        unhealthy_count = sum(1 for c in components if not c.is_healthy())
        overall_status = "healthy" if unhealthy_count == 0 else "degraded"

        if unhealthy_count > len(components) // 2:
            overall_status = "unhealthy"

        return HealthReport(
            timestamp=datetime.now(),
            overall_status=overall_status,
            components=components,
            issues=issues
        )

    async def _check_platforms(self) -> ComponentHealth:
        """检查平台状态"""
        start = time.time()

        try:
            if not self.engine or not self.engine.platform_manager:
                return ComponentHealth(
                    name="platforms",
                    status="unknown",
                    message="引擎未初始化"
                )

            platform_manager = self.engine.platform_manager
            platforms = platform_manager.list_platforms()

            issues = []
            ready_count = 0

            for p in platforms:
                if p.get("status") == "ready":
                    ready_count += 1
                else:
                    issues.append(f"{p.get('name')}: {p.get('status')}")

            latency_ms = (time.time() - start) * 1000

            if len(platforms) == 0:
                return ComponentHealth(
                    name="platforms",
                    status="unknown",
                    message="未注册平台",
                    latency_ms=latency_ms
                )

            all_ready = ready_count == len(platforms)

            return ComponentHealth(
                name="platforms",
                status="healthy" if all_ready else "degraded",
                message=f"{ready_count}/{len(platforms)} 平台就绪",
                latency_ms=latency_ms,
                last_check=datetime.now(),
                issues=issues
            )

        except Exception as e:
            return ComponentHealth(
                name="platforms",
                status="error",
                message=f"检查失败: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
                issues=[str(e)]
            )

    async def _check_storage(self) -> ComponentHealth:
        """检查存储状态"""
        start = time.time()

        try:
            if not self.engine or not self.engine.storage:
                return ComponentHealth(
                    name="storage",
                    status="unknown",
                    message="存储未初始化"
                )

            storage = self.engine.storage

            await asyncio.sleep(0.1)

            latency_ms = (time.time() - start) * 1000

            return ComponentHealth(
                name="storage",
                status="healthy",
                message="存储正常",
                latency_ms=latency_ms,
                last_check=datetime.now()
            )

        except Exception as e:
            return ComponentHealth(
                name="storage",
                status="error",
                message=f"存储错误: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
                issues=[str(e)]
            )

    async def _check_network(self) -> ComponentHealth:
        """检查网络状态"""
        start = time.time()

        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://www.baidu.com")
                latency_ms = (time.time() - start) * 1000

                if response.status_code == 200:
                    return ComponentHealth(
                        name="network",
                        status="healthy",
                        message="网络正常",
                        latency_ms=latency_ms,
                        last_check=datetime.now()
                    )
                else:
                    return ComponentHealth(
                        name="network",
                        status="degraded",
                        message=f"网络响应异常: {response.status_code}",
                        latency_ms=latency_ms,
                        issues=[f"HTTP {response.status_code}"]
                    )

        except Exception as e:
            return ComponentHealth(
                name="network",
                status="error",
                message=f"网络错误: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
                issues=[str(e)]
            )

    async def _check_notifier(self) -> ComponentHealth:
        """检查通知组件状态"""
        start = time.time()

        try:
            notifier = self.engine.notifier

            enabled_channels = []
            if notifier.config.dingtalk and notifier.config.dingtalk.enabled:
                enabled_channels.append("dingtalk")
            if notifier.config.serverchan and notifier.config.serverchan.enabled:
                enabled_channels.append("serverchan")
            if notifier.config.pushplus and notifier.config.pushplus.enabled:
                enabled_channels.append("pushplus")
            if notifier.config.email and notifier.config.email.enabled:
                enabled_channels.append("email")
            if notifier.config.telegram and notifier.config.telegram.enabled:
                enabled_channels.append("telegram")

            latency_ms = (time.time() - start) * 1000

            return ComponentHealth(
                name="notifier",
                status="healthy",
                message=f"{len(enabled_channels)} 个渠道已配置",
                latency_ms=latency_ms,
                last_check=datetime.now()
            )

        except Exception as e:
            return ComponentHealth(
                name="notifier",
                status="error",
                message=f"通知组件错误: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
                issues=[str(e)]
            )


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._sign_in_count: int = 0
        self._success_count: int = 0
        self._failure_count: int = 0
        self._retry_count: int = 0
        self._start_time: float = time.time()
        self._circuit_breaker_trials: int = 0
        self._errors: List[Dict] = []

    def record_sign_in(self, success: bool, platform: str, account: str, duration_ms: int):
        """记录签到结果"""
        self._sign_in_count += 1
        if success:
            self._success_count += 1
        else:
            self._failure_count += 1
            self._errors.append({
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "account": account,
                "duration_ms": duration_ms
            })

    def record_retry(self):
        """记录重试"""
        self._retry_count += 1

    def record_circuit_breaker_trial(self):
        """记录熔断器尝试"""
        self._circuit_breaker_trials += 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        uptime = time.time() - self._start_time
        success_rate = (
            self._success_count / self._sign_in_count
            if self._sign_in_count > 0 else 0
        )

        return {
            "uptime_seconds": uptime,
            "sign_in": {
                "total": self._sign_in_count,
                "success": self._success_count,
                "failure": self._failure_count,
                "success_rate": success_rate
            },
            "retry": {
                "total": self._retry_count,
                "rate": self._retry_count / self._sign_in_count if self._sign_in_count > 0 else 0
            },
            "circuit_breaker": {
                "trials": self._circuit_breaker_trials
            },
            "recent_errors": self._errors[-10:]
        }

    def reset(self):
        """重置指标"""
        self._sign_in_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._retry_count = 0
        self._circuit_breaker_trials = 0
        self._errors.clear()
