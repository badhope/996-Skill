"""
哔哩哔哩签到
"""

from typing import Dict, Any

from loguru import logger

from .base import BasePlatform


class BilibiliPlatform(BasePlatform):
    """哔哩哔哩签到"""
    
    name = "bilibili"
    base_url = "https://api.bilibili.com"
    
    async def sign_in(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """执行哔哩哔哩签到"""
        headers = {
            "Cookie": f"SESSDATA={account.get('sessdata', '')}; "
                      f"bili_jct={account.get('bili_jct', '')}; "
                      f"buvid3={account.get('buvid3', '')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com"
        }
        
        try:
            # 签到请求
            url = f"{self.base_url}/pgc/activity/score/task/sign"
            
            async with self.session or aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers) as resp:
                    data = await resp.json()
                    
                    if data.get("code") == 0:
                        return {
                            "success": True,
                            "message": "签到成功",
                            "data": data.get("data", {})
                        }
                    elif data.get("code") == -101:
                        return {
                            "success": False,
                            "message": "Cookie 已过期，请重新获取"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"签到失败: {data.get('message', '未知错误')}"
                        }
        except Exception as e:
            logger.error(f"哔哩哔哩签到异常: {e}")
            return {
                "success": False,
                "message": f"请求异常: {str(e)}"
            }
