"""
平台管理器
负责平台的注册、发现、生命周期管理
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Callable

from autosignin.platforms.base import BasePlatform, PlatformInstance, PlatformMetadata


logger = logging.getLogger(__name__)


class PlatformStatus:
    DISCOVERED = "discovered"
    LOADED = "loaded"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


class PlatformManager:
    """平台管理器"""
    
    def __init__(self):
        self._platforms: Dict[str, PlatformInstance] = {}
        self._instances: Dict[str, BasePlatform] = {}
        self._lock = asyncio.Lock()
    
    def register(
        self,
        name: str,
        cls: Type[BasePlatform],
        metadata: PlatformMetadata = None
    ) -> None:
        """注册平台"""
        if metadata is None:
            metadata = cls.metadata or PlatformMetadata(
                name=name,
                display_name=getattr(cls, 'display_name', name),
                version=getattr(cls, 'version', '1.0.0')
            )
        
        instance = PlatformInstance(
            metadata=metadata,
            cls=cls,
            status=PlatformStatus.DISCOVERED
        )
        
        self._platforms[name] = instance
        logger.info(f"Platform registered: {name} v{metadata.version}")
    
    def register_instance(self, platform: BasePlatform) -> None:
        """注册平台实例"""
        name = platform.name
        self._instances[name] = platform
        
        if name in self._platforms:
            self._platforms[name].status = PlatformStatus.LOADED
        else:
            self._platforms[name] = PlatformInstance(
                metadata=platform.metadata,
                cls=type(platform),
                status=PlatformStatus.LOADED
            )
        
        logger.info(f"Platform instance registered: {name}")
    
    async def initialize_platform(self, name: str) -> bool:
        """初始化平台"""
        async with self._lock:
            if name not in self._platforms:
                logger.error(f"Platform not found: {name}")
                return False
            
            platform_instance = self._platforms[name]
            
            try:
                if name not in self._instances:
                    self._instances[name] = platform_instance.cls()
                
                platform = self._instances[name]
                
                if hasattr(platform, 'initialize'):
                    await platform.initialize()
                
                platform_instance.status = PlatformStatus.READY
                platform_instance.last_used = platform_instance.last_used or None
                
                logger.info(f"Platform initialized: {name}")
                return True
                
            except Exception as e:
                platform_instance.status = PlatformStatus.ERROR
                platform_instance.error_message = str(e)
                logger.error(f"Failed to initialize platform {name}: {e}")
                return False
    
    async def get_platform(self, name: str) -> Optional[BasePlatform]:
        """获取平台实例"""
        if name not in self._instances:
            if name not in self._platforms:
                return None
            
            await self.initialize_platform(name)
        
        return self._instances.get(name)
    
    def get_platform_info(self, name: str) -> Optional[Dict]:
        """获取平台信息"""
        if name not in self._platforms:
            return None
        return self._platforms[name].to_dict()
    
    def list_platforms(self) -> List[Dict]:
        """列出所有平台"""
        return [p.to_dict() for p in self._platforms.values()]
    
    async def cleanup_platform(self, name: str) -> bool:
        """清理平台资源"""
        async with self._lock:
            if name not in self._instances:
                return True
            
            platform = self._instances[name]
            
            try:
                if hasattr(platform, 'cleanup'):
                    await platform.cleanup()
                
                del self._instances[name]
                logger.info(f"Platform cleaned up: {name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cleanup platform {name}: {e}")
                return False
    
    @property
    def platform_count(self) -> int:
        return len(self._platforms)


PLATFORM_REGISTRY: Dict[str, Type[BasePlatform]] = {}


def register(name: str = None, **kwargs):
    """全局注册装饰器"""
    def decorator(cls: Type[BasePlatform]) -> Type[BasePlatform]:
        platform_name = name or getattr(cls, 'name', None) or cls.__name__.lower()
        PLATFORM_REGISTRY[platform_name] = cls
        return cls
    return decorator


__all__ = ["PlatformManager", "PlatformStatus", "register"]
