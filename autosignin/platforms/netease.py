"""
网易云音乐平台插件
"""

import http.cookies
from typing import Dict, Any

import httpx

from autosignin.platforms.base import BasePlatform, register_platform
from autosignin.models.signin import SignInResult


@register_platform(
    name="netease_music",
    display_name="网易云音乐",
    version="1.1.0",
    capabilities=["daily_sign", "listen_songs"],
    required_fields=["cookie"]
)
class NeteaseMusicPlatform(BasePlatform):
    """网易云音乐签到平台"""
    
    name = "netease_music"
    display_name = "网易云音乐"
    version = "1.1.0"
    base_url = "https://music.163.com"
    
    async def sign_in(self, account_name: str, cookies: Dict[str, str]) -> SignInResult:
        """执行网易云音乐签到"""
        result = SignInResult(
            platform=self.name,
            account=account_name
        )
        
        cookie_str = cookies.get("cookie", "")
        
        if not cookie_str:
            result.success = False
            result.error = "Missing required cookie"
            result.error_type = "AuthError"
            return result
        
        headers = {
            "Cookie": cookie_str,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/weapi/point/dailyTask",
                    data={"type": 0},
                    headers=headers
                )
                
                result.status_code = response.status_code
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == 200:
                        result.success = True
                        result.message = "签到成功"
                        result.data = data
                    elif data.get("code") == -2:
                        result.success = False
                        result.error = "签到失败: 重复签到"
                        result.error_type = "SignInError"
                    elif data.get("code") == 301:
                        result.success = False
                        result.error = "登录状态已失效"
                        result.error_type = "AuthError"
                    else:
                        result.success = False
                        result.error = f"签到失败: {data.get('msg', '未知错误')}"
                        result.error_type = "SignInError"
                else:
                    result.success = False
                    result.error = f"HTTP错误: {response.status_code}"
                    result.error_type = "NetworkError"
                    
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
        cookie_str = cookies.get("cookie", "")
        
        if not cookie_str:
            return False
        
        headers = {
            "Cookie": cookie_str,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/weapi/w/nuser/account/get",
                    data={},
                    headers=headers
                )
                
                data = response.json()
                return data.get("code") == 200
                
        except Exception:
            return False
