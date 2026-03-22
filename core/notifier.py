"""
通知管理器 - 支持多种通知方式
"""

import json
from typing import Dict, Any, List

import aiohttp
from loguru import logger


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send(self, results: List[Dict[str, Any]]):
        """发送通知"""
        # 构建消息
        message = self._build_message(results)
        
        # 钉钉
        if self.config.get("dingtalk", {}).get("enabled"):
            await self._send_dingtalk(message)
        
        # Server酱
        if self.config.get("serverchan", {}).get("enabled"):
            await self._send_serverchan(message)
        
        # PushPlus
        if self.config.get("pushplus", {}).get("enabled"):
            await self._send_pushplus(message)
        
        # 邮件
        if self.config.get("email", {}).get("enabled"):
            await self._send_email(message)
    
    def _build_message(self, results: List[Dict[str, Any]]) -> Dict[str, str]:
        """构建通知消息"""
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        
        title = f"签到完成: {success_count}/{total_count} 成功"
        
        content_lines = []
        for r in results:
            status = "✅" if r.get("success") else "❌"
            content_lines.append(
                f"{status} {r['platform']} - {r['account']}: {r.get('message', '')}"
            )
        
        content = "\n".join(content_lines)
        
        return {"title": title, "content": content}
    
    async def _send_dingtalk(self, message: Dict[str, str]):
        """发送钉钉通知"""
        config = self.config["dingtalk"]
        webhook = config["webhook"]
        secret = config.get("secret", "")
        
        # 构建签名（简化版，实际需要加时间戳和签名）
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": message["title"],
                "text": f"### {message['title']}\n\n{message['content']}"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook, json=payload) as resp:
                if resp.status == 200:
                    logger.info("钉钉通知发送成功")
                else:
                    logger.error(f"钉钉通知发送失败: {resp.status}")
    
    async def _send_serverchan(self, message: Dict[str, str]):
        """发送 Server酱通知"""
        config = self.config["serverchan"]
        key = config["key"]
        url = f"https://sctapi.ftqq.com/{key}.send"
        
        payload = {
            "title": message["title"],
            "desp": message["content"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                if resp.status == 200:
                    logger.info("Server酱通知发送成功")
    
    async def _send_pushplus(self, message: Dict[str, str]):
        """发送 PushPlus通知"""
        config = self.config["pushplus"]
        token = config["token"]
        url = "http://www.pushplus.plus/send"
        
        payload = {
            "token": token,
            "title": message["title"],
            "content": message["content"]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.info("PushPlus通知发送成功")
    
    async def _send_email(self, message: Dict[str, str]):
        """发送邮件通知（简化版）"""
        # 实际实现需要使用 smtplib
        logger.info("邮件通知已跳过（需要额外配置）")
