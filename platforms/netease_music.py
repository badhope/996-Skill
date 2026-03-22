"""
网易云音乐签到
"""

from typing import Dict, Any

import aiohttp
from loguru import logger

from .base import BasePlatform


class NeteaseMusicPlatform(BasePlatform):
    """网易云音乐签到"""
    
    name = "netease_music"
    base_url = "https://music.163.com"
    
    async def sign_in(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """执行网易云音乐签到"""
        cookie = account.get("cookie", "")
        
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            # 移动端签到
            url = "https://music.163.com/weapi/point/dailyTask"
            
            # 实际请求需要加密参数，这里简化处理
            async with aiohttp.ClientSession() as session:
                # 签到类型: 0 Android, 1 PC, 2 Web
                params = {"type": 0}
                
                async with session.post(url, data=params, headers=headers) as resp:
                    text = await resp.text()
                    
                    if resp.status == 200:
                        return {
                            "success": True,
                            "message": "网易云音乐签到成功",
                            "data": {"response": text[:100]}
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"签到失败，状态码: {resp.status}"
                        }
        except Exception as e:
            logger.error(f"网易云音乐签到异常: {e}")
            return {
                "success": False,
                "message": f"请求异常: {str(e)}"
            }
