"""
Platforms 模块 - 各平台签到实现
"""

from typing import Dict, Type, Optional
from .base import BasePlatform
from .bilibili import BilibiliPlatform
from .netease_music import NeteaseMusicPlatform

# 平台注册表
PLATFORM_REGISTRY: Dict[str, Type[BasePlatform]] = {
    "bilibili": BilibiliPlatform,
    "netease_music": NeteaseMusicPlatform,
}


def get_platform(name: str) -> Optional[BasePlatform]:
    """获取平台实例"""
    platform_class = PLATFORM_REGISTRY.get(name)
    if platform_class:
        return platform_class()
    return None


def register_platform(name: str, platform_class: Type[BasePlatform]):
    """注册新平台"""
    PLATFORM_REGISTRY[name] = platform_class


__all__ = [
    "BasePlatform",
    "BilibiliPlatform",
    "NeteaseMusicPlatform",
    "get_platform",
    "register_platform",
]
