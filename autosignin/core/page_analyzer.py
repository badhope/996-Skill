"""
页面内容分析器
检测跳转广告、UI变化、登录失效等用户体验问题
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

import httpx


@dataclass
class AnalysisResult:
    """分析结果"""
    platform: str
    has_ad_redirect: bool = False
    login_expired: bool = False
    loading_failed: bool = False
    ui_changed: bool = False
    captcha_detected: bool = False
    rate_limited: bool = False
    issues: List[str] = field(default_factory=list)
    severity: str = "info"

    def has_critical_issue(self) -> bool:
        """是否有严重问题"""
        return self.has_ad_redirect or self.login_expired or self.captcha_detected


class PageAnalyzer:
    """页面内容分析器"""

    AD_PATTERNS = [
        "跳转中",
        "正在跳转",
        "loading",
        "ad.",
        "advertisement",
        "sponsor",
        "推广",
        "广告",
        "redirect",
        "forwarding",
    ]

    ERROR_PATTERNS = [
        "页面不存在",
        "404",
        "403",
        "访问被拒绝",
        "请登录",
        "登录失效",
        "网络异常",
        "系统繁忙",
        "稍后重试",
    ]

    LOGIN_PATTERNS = [
        "登录",
        "login",
        "请先登录",
        "请登录",
        "未登录",
        "授权",
        "authorize",
        "passport",
        "signin",
    ]

    CAPTCHA_PATTERNS = [
        "验证码",
        "captcha",
        "验证",
        "安全验证",
        "人机验证",
        "滑动验证",
        "点选验证",
    ]

    RATE_LIMIT_PATTERNS = [
        "请求过于频繁",
        "rate limit",
        "too many requests",
        "429",
        "请稍后",
        "访问受限",
    ]

    def __init__(self):
        self._platform_specific_elements: Dict[str, List[str]] = {
            "bilibili": ["bilibili", "B站", "bili", "小破站"],
            "netease_music": ["网易云", "music.163", "云音乐"],
            "zhihu": ["知乎", "zhihu", "问答"],
            "juejin": ["掘金", "juejin", "稀土"],
            "v2ex": ["V2EX", "v2ex", "way to explore"],
        }

    def analyze_response(
        self,
        response: httpx.Response,
        platform: str
    ) -> AnalysisResult:
        """分析响应内容"""
        result = AnalysisResult(platform=platform)

        content = response.text.lower() if response.text else ""
        url = str(response.url).lower()
        status_code = response.status_code
        elapsed_ms = response.elapsed.total_seconds() * 1000

        if status_code == 403:
            result.rate_limited = True
            result.issues.append("访问被拒绝 (HTTP 403)")
            result.severity = "warning"

        elif status_code == 429:
            result.rate_limited = True
            result.issues.append("请求过于频繁 (HTTP 429)")
            result.severity = "warning"

        elif status_code >= 500:
            result.loading_failed = True
            result.issues.append(f"服务器错误 (HTTP {status_code})")
            result.severity = "error"

        if self._detect_ad_redirect(response, elapsed_ms, content):
            result.has_ad_redirect = True
            result.issues.append("检测到广告跳转")
            result.severity = "warning"

        if self._detect_login_expired(content, url):
            result.login_expired = True
            result.issues.append("登录状态已失效")
            result.severity = "error"

        if self._detect_captcha(content, url):
            result.captcha_detected = True
            result.issues.append("检测到验证码拦截")
            result.severity = "error"

        if self._detect_rate_limit(content, url):
            result.rate_limited = True
            result.issues.append("检测到频率限制")
            result.severity = "warning"

        if self._detect_ui_change(content, url, platform):
            result.ui_changed = True
            result.issues.append("页面 UI 可能已变更")
            result.severity = "info"

        return result

    def _detect_ad_redirect(
        self,
        response: httpx.Response,
        elapsed_ms: float,
        content: str
    ) -> bool:
        """检测广告跳转"""
        url = str(response.url)

        redirect_params = ["url=", "redirect=", "target=", "to="]
        for param in redirect_params:
            if param in url:
                return True

        if elapsed_ms < 500:
            for pattern in self.AD_PATTERNS:
                if pattern.lower() in content:
                    return True

        if response.headers.get("location"):
            return True

        return False

    def _detect_login_expired(self, content: str, url: str) -> bool:
        """检测登录失效"""
        for indicator in self.LOGIN_PATTERNS:
            if indicator.lower() in url:
                return True

        for pattern in self.ERROR_PATTERNS:
            if pattern.lower() in content and ("登录" in content or "login" in content):
                return True

        login_urls = ["passport", "login", "signin", "auth", "account"]
        for login_url in login_urls:
            if login_url in url:
                return True

        return False

    def _detect_captcha(self, content: str, url: str) -> bool:
        """检测验证码"""
        for pattern in self.CAPTCHA_PATTERNS:
            if pattern.lower() in content:
                return True

        captcha_urls = ["captcha", "verify", "challenge"]
        for captcha_url in captcha_urls:
            if captcha_url in url:
                return True

        return False

    def _detect_rate_limit(self, content: str, url: str) -> bool:
        """检测频率限制"""
        for pattern in self.RATE_LIMIT_PATTERNS:
            if pattern.lower() in content:
                return True

        return False

    def _detect_ui_change(
        self,
        content: str,
        url: str,
        platform: str
    ) -> bool:
        """检测 UI 变化"""
        expected_elements = self._platform_specific_elements.get(platform, [])

        if not expected_elements:
            return False

        found_count = 0
        for element in expected_elements:
            if element.lower() in content:
                found_count += 1

        return found_count < len(expected_elements) * 0.5

    def should_retry(self, result: AnalysisResult) -> bool:
        """判断是否应该重试"""
        if result.loading_failed:
            return True
        if result.rate_limited:
            return True
        if result.login_expired:
            return False
        if result.captcha_detected:
            return False
        if result.has_ad_redirect:
            return False
        return False

    def get_retry_delay(self, result: AnalysisResult) -> int:
        """获取重试延迟时间（秒）"""
        if result.rate_limited:
            return 60
        if result.loading_failed:
            return 5
        return 30
