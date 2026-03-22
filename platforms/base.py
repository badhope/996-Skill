"""
平台基类 - 所有签到平台的基础
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

import aiohttp
from loguru import logger


class BasePlatform(ABC):
    """平台基类"""
    
    name: str = ""
    base_url: str = ""
    
    def __init__(self):
        self.session: aiohttp.ClientSession = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def sign_in(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行签到
        
        Returns:
            {
                "success": bool,
                "message": str,
                "data": Any (optional)
            }
        """
        pass
    
    async def http_get(self, url: str, headers: Dict[str, str] = None) -> aiohttp.ClientResponse:
        """HTTP GET 请求"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.get(url, headers=headers) as resp:
            return resp
    
    async def http_post(self, url: str, data: Dict[str, Any] = None, 
                        headers: Dict[str, str] = None) -> aiohttp.ClientResponse:
        """HTTP POST 请求"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(url, json=data, headers=headers) as resp:
            return resp
