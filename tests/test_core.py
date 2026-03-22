"""
核心模块测试
"""

import pytest
from core.scheduler import TaskScheduler
from core.notifier import NotificationManager


def test_scheduler_init():
    """测试调度器初始化"""
    config = {"cron": "0 9 * * *"}
    scheduler = TaskScheduler(config)
    assert scheduler.cron == "0 9 * * *"


def test_notifier_init():
    """测试通知管理器初始化"""
    config = {
        "dingtalk": {"enabled": False},
        "serverchan": {"enabled": False}
    }
    notifier = NotificationManager(config)
    assert notifier.config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
