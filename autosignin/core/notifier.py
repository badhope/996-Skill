"""
通知管理器
统一管理多渠道通知发送
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx

from autosignin.config.models import (
    NotificationConfig,
    DingTalkConfig,
    ServerChanConfig,
    PushPlusConfig,
    EmailConfig,
    TelegramConfig
)
from autosignin.models.signin import SignInResult


logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """通知渠道基类"""
    
    def __init__(self, config: Any):
        self.config = config
        self.enabled = getattr(config, 'enabled', False)
    
    @abstractmethod
    async def send(self, title: str, content: str, **kwargs) -> bool:
        """发送通知"""
        pass


@dataclass
class NotificationTemplate:
    """通知模板"""
    title: str
    content: str
    format: str = "text"


class DingTalkChannel(NotificationChannel):
    """钉钉通知渠道"""
    
    def __init__(self, config: DingTalkConfig):
        super().__init__(config)
        self.webhook = config.webhook
        self.secret = config.secret
        self.at_mobiles = config.at_mobiles
        self.is_at_all = config.is_at_all
    
    async def send(self, title: str, content: str, **kwargs) -> bool:
        """发送钉钉通知"""
        if not self.enabled or not self.webhook:
            return False
        
        try:
            import hashlib
            import time
            import base64
            import hmac
            
            timestamp = str(round(time.time() * 1000))
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = f'{timestamp}\n{self.secret}'
            string_to_sign_enc = string_to_sign.encode('utf-8')
            
            hmac_code = hmac.new(
                secret_enc, 
                string_to_sign_enc, 
                digestmod=hashlib.sha256
            ).digest()
            
            sign = base64.b64encode(hmac_code).decode('utf-8')
            
            url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
            
            message = {
                "msgtype": "text",
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }
            
            if self.at_mobiles or self.is_at_all:
                message["at"] = {
                    "atMobiles": self.at_mobiles,
                    "isAtAll": self.is_at_all
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=message,
                    timeout=10.0
                )
                result = response.json()
                
                if result.get("errcode") == 0:
                    logger.info(f"DingTalk notification sent: {title}")
                    return True
                else:
                    logger.error(f"DingTalk error: {result.get('errmsg')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send DingTalk notification: {e}")
            return False


class ServerChanChannel(NotificationChannel):
    """Server酱通知渠道"""
    
    def __init__(self, config: ServerChanConfig):
        super().__init__(config)
        self.key = config.key
    
    async def send(self, title: str, content: str, **kwargs) -> bool:
        """发送 Server酱通知"""
        if not self.enabled or not self.key:
            return False
        
        try:
            url = f"https://sctapi.ftqq.com/{self.key}.send"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={
                        "title": title,
                        "desp": content
                    },
                    timeout=10.0
                )
                result = response.json()
                
                if result.get("code") == 0:
                    logger.info(f"ServerChan notification sent: {title}")
                    return True
                else:
                    logger.error(f"ServerChan error: {result.get('msg')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send ServerChan notification: {e}")
            return False


class PushPlusChannel(NotificationChannel):
    """PushPlus 通知渠道"""
    
    def __init__(self, config: PushPlusConfig):
        super().__init__(config)
        self.token = config.token
    
    async def send(self, title: str, content: str, **kwargs) -> bool:
        """发送 PushPlus 通知"""
        if not self.enabled or not self.token:
            return False
        
        try:
            url = "https://www.pushplus.plus/send"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "token": self.token,
                        "title": title,
                        "content": content
                    },
                    timeout=10.0
                )
                result = response.json()
                
                if result.get("code") == 0:
                    logger.info(f"PushPlus notification sent: {title}")
                    return True
                else:
                    logger.error(f"PushPlus error: {result.get('msg')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send PushPlus notification: {e}")
            return False


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""
    
    def __init__(self, config: EmailConfig):
        super().__init__(config)
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.sender = config.sender
        self.password = config.password
        self.receiver = config.receiver
    
    async def send(self, title: str, content: str, **kwargs) -> bool:
        """发送邮件通知"""
        if not self.enabled or not self.sender or not self.receiver:
            return False
        
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message["From"] = self.sender
            message["To"] = self.receiver
            message["Subject"] = title
            
            body = MIMEText(content, "plain", "utf-8")
            message.attach(body)
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.sender,
                password=self.password,
                start_tls=True
            )
            
            logger.info(f"Email notification sent: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class TelegramChannel(NotificationChannel):
    """Telegram 通知渠道"""
    
    def __init__(self, config: TelegramConfig):
        super().__init__(config)
        self.bot_token = config.bot_token
        self.chat_id = config.chat_id
    
    async def send(self, title: str, content: str, **kwargs) -> bool:
        """发送 Telegram 通知"""
        if not self.enabled or not self.bot_token or not self.chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            text = f"*{title}*\n\n{content}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"Telegram notification sent: {title}")
                    return True
                else:
                    logger.error(f"Telegram error: {result.get('description')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self._channels: Dict[str, NotificationChannel] = {}
        
        self._init_channels()
        
        self._rate_limiter: Optional[Any] = None
        self._queue: asyncio.Queue = None
        self._worker_task: Optional[asyncio.Task] = None
    
    def _init_channels(self):
        """初始化通知渠道"""
        self._channels["dingtalk"] = DingTalkChannel(self.config.dingtalk)
        self._channels["serverchan"] = ServerChanChannel(self.config.serverchan)
        self._channels["pushplus"] = PushPlusChannel(self.config.pushplus)
        self._channels["email"] = EmailChannel(self.config.email)
        self._channels["telegram"] = TelegramChannel(self.config.telegram)
    
    def _default_templates(self) -> Dict[str, NotificationTemplate]:
        """默认模板"""
        return {
            "sign_in_success": NotificationTemplate(
                title="✅ 签到成功",
                content="{platform} - {account}\n时间: {timestamp}\n消息: {message}"
            ),
            "sign_in_failed": NotificationTemplate(
                title="❌ 签到失败",
                content="{platform} - {account}\n时间: {timestamp}\n错误: {error}"
            ),
            "summary": NotificationTemplate(
                title="📊 签到汇总",
                content="总任务: {total}\n成功: {success}\n失败: {failed}\n耗时: {duration_ms}ms"
            )
        }
    
    async def send(
        self,
        channel: str = None,
        title: str = "",
        content: str = "",
        **kwargs
    ) -> bool:
        """发送通知"""
        if channel:
            if channel in self._channels:
                return await self._channels[channel].send(title, content, **kwargs)
            return False
        
        results = []
        for ch in self._channels.values():
            if ch.enabled:
                results.append(await ch.send(title, content, **kwargs))
        
        return any(results) if results else False
    
    async def send_sign_in_result(self, result: SignInResult) -> bool:
        """发送签到结果通知"""
        if result.success:
            title = f"✅ 签到成功 - {result.platform}"
            content = (
                f"账号: {result.account}\n"
                f"时间: {result.timestamp}\n"
                f"消息: {result.message}"
            )
        else:
            title = f"❌ 签到失败 - {result.platform}"
            content = (
                f"账号: {result.account}\n"
                f"时间: {result.timestamp}\n"
                f"错误: {result.error or result.message}"
            )
        
        return await self.send(title=title, content=content)
    
    async def send_summary(
        self,
        results: List[SignInResult],
        duration_ms: int = 0
    ) -> bool:
        """发送签到汇总"""
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        title = "📊 签到汇总报告"
        content = (
            f"总任务: {len(results)}\n"
            f"成功: {success_count}\n"
            f"失败: {failed_count}\n"
            f"总耗时: {duration_ms}ms"
        )
        
        return await self.send(title=title, content=content)
    
    def get_enabled_channels(self) -> List[str]:
        """获取已启用的渠道"""
        return [name for name, ch in self._channels.items() if ch.enabled]


__all__ = [
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationManager",
    "DingTalkChannel",
    "ServerChanChannel",
    "PushPlusChannel",
    "EmailChannel",
    "TelegramChannel",
]
