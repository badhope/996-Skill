"""
哔哩哔哩平台插件
"""

from typing import Dict, Any

import httpx

from autosignin.platforms.base import BasePlatform, register_platform
from autosignin.models.signin import SignInResult


@register_platform(
    name="bilibili",
    display_name="哔哩哔哩",
    version="1.2.0",
    capabilities=["daily_sign", "watch_video", "share_video"],
    required_fields=["sessdata", "bili_jct"]
)
class BilibiliPlatform(BasePlatform):
    """哔哩哔哩签到平台"""
    
    name = "bilibili"
    display_name = "哔哩哔哩"
    version = "1.2.0"
    base_url = "https://api.bilibili.com"
    
    async def sign_in(self, account_name: str, cookies: Dict[str, str]) -> SignInResult:
        """执行哔哩哔哩签到"""
        result = SignInResult(
            platform=self.name,
            account=account_name
        )
        
        sessdata = cookies.get("sessdata", "")
        bili_jct = cookies.get("bili_jct", "")
        buvid3 = cookies.get("buvid3", "")
        
        if not sessdata or not bili_jct:
            result.success = False
            result.error = "Missing required cookies: sessdata or bili_jct"
            result.error_type = "AuthError"
            return result
        
        headers = {
            "Cookie": f"SESSDATA={sessdata}; bili_jct={bili_jct}; buvid3={buvid3}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/pgc/activity/score/task/sign",
                    headers=headers
                )
                
                data = response.json()
                result.status_code = response.status_code
                
                if data.get("code") == 0:
                    result.success = True
                    result.message = "签到成功"
                    result.data = data.get("data", {})
                elif data.get("code") == -101:
                    result.success = False
                    result.error = "Cookie已过期，请重新获取"
                    result.error_type = "AuthError"
                elif data.get("code") == -400:
                    result.success = False
                    result.error = "请求参数错误"
                    result.error_type = "ValidationError"
                else:
                    result.success = False
                    result.error = f"签到失败: {data.get('message', '未知错误')}"
                    result.error_type = "SignInError"
                    
        except httpx.TimeoutException:
            result.success = False
            result.error = "请求超时"
            result.error_type = "TimeoutError"
        except httpx.HTTPError as e:
            result.success = False
            result.error = f"HTTP错误: {str(e)}"
            result.error_type = "NetworkError"
        except Exception as e:
            result.success = False
            result.error = f"签到异常: {str(e)}"
            result.error_type = "UnknownError"
        
        return result
    
    async def verify(self, cookies: Dict[str, str]) -> bool:
        """验证登录状态"""
        sessdata = cookies.get("sessdata", "")
        
        if not sessdata:
            return False
        
        headers = {
            "Cookie": f"SESSDATA={sessdata}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.bilibili.com/x/web-interface/nav",
                    headers=headers
                )
                
                data = response.json()
                return data.get("code") == 0 and data.get("data", {}).get("isLogin", False)
                
        except Exception:
            return False
