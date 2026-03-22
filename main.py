#!/usr/bin/env python3
"""
Auto-SignIn - 多平台自动签到系统
主程序入口
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import List, Dict, Any

import yaml
from loguru import logger

from core.scheduler import TaskScheduler
from core.notifier import NotificationManager
from platforms import get_platform


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yml"
    
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        logger.info("请复制 config.example.yml 为 config.yml 并配置")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def run_sign_in(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """执行所有签到任务"""
    results = []
    accounts = config.get("accounts", {})
    
    for platform_name, platform_accounts in accounts.items():
        if not platform_accounts:
            continue
            
        platform = get_platform(platform_name)
        if not platform:
            logger.warning(f"不支持的平台: {platform_name}")
            continue
        
        logger.info(f"开始执行 {platform_name} 签到...")
        
        for account in platform_accounts:
            try:
                result = await platform.sign_in(account)
                results.append({
                    "platform": platform_name,
                    "account": account.get("name", "unknown"),
                    **result
                })
            except Exception as e:
                logger.error(f"{platform_name} 签到失败: {e}")
                results.append({
                    "platform": platform_name,
                    "account": account.get("name", "unknown"),
                    "success": False,
                    "message": str(e)
                })
    
    return results


async def main():
    """主函数"""
    logger.info("🚀 Auto-SignIn 启动")
    
    # 加载配置
    config = load_config()
    
    # 初始化通知管理器
    notifier = NotificationManager(config.get("notifications", {}))
    
    # 初始化任务调度器
    scheduler = TaskScheduler(config.get("schedule", {}))
    
    # 定义签到任务
    async def sign_in_task():
        results = await run_sign_in(config)
        
        # 统计结果
        success_count = sum(1 for r in results if r.get("success"))
        total_count = len(results)
        
        logger.info(f"签到完成: {success_count}/{total_count} 成功")
        
        # 发送通知
        await notifier.send(results)
        
        return results
    
    # 注册任务
    scheduler.add_job(sign_in_task)
    
    # 立即执行一次
    await sign_in_task()
    
    # 启动调度器
    scheduler.start()
    
    # 等待中断信号
    stop_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info("收到停止信号，正在关闭...")
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await stop_event.wait()
    scheduler.stop()
    logger.info("👋 Auto-SignIn 已停止")


if __name__ == "__main__":
    asyncio.run(main())
