"""平台模块"""

from autosignin.platforms.base import BasePlatform, register_platform
from autosignin.platforms.manager import PlatformManager
from autosignin.models.signin import SignInResult

__all__ = ["BasePlatform", "SignInResult", "register_platform", "PlatformManager"]
