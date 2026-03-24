"""平台模块"""

from autosignin.platforms.base import BasePlatform, SignInResult, register_platform
from autosignin.platforms.manager import PlatformManager

__all__ = ["BasePlatform", "SignInResult", "register_platform", "PlatformManager"]
