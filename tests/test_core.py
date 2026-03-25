"""
核心模块测试
"""

import pytest
import asyncio
from datetime import datetime

from autosignin.core.scheduler import TaskScheduler
from autosignin.core.notifier import NotificationManager
from autosignin.core.storage import SQLiteStorageAdapter
from autosignin.core.exceptions import SignInException, AuthError, RateLimitError
from autosignin.config.models import NotificationConfig, DingTalkConfig, ServerChanConfig
from autosignin.models.signin import SignInRecord, SignInResult, SignInTask, TaskStatus


class TestTaskScheduler:
    """调度器测试"""
    
    def test_scheduler_init(self):
        """测试调度器初始化"""
        scheduler = TaskScheduler()
        assert scheduler is not None
        assert scheduler._scheduler is not None
    
    def test_register_handler(self):
        """测试注册处理器"""
        scheduler = TaskScheduler()
        
        async def dummy_handler():
            pass
        
        scheduler.register_handler("test", dummy_handler)
        assert "test" in scheduler._handlers
    
    def test_add_cron_job(self):
        """测试添加Cron任务"""
        scheduler = TaskScheduler()
        
        async def dummy_handler():
            pass
        
        scheduler.register_handler("sign_in", dummy_handler)
        scheduler.add_cron_job(
            job_id="test_job",
            handler_name="sign_in",
            cron_expression="0 9 * * *"
        )
        
        assert "test_job" in scheduler._tasks


class TestNotificationManager:
    """通知管理器测试"""
    
    def test_notifier_init(self):
        """测试通知管理器初始化"""
        config = NotificationConfig(
            dingtalk=DingTalkConfig(enabled=False),
            serverchan=ServerChanConfig(enabled=False)
        )
        notifier = NotificationManager(config)
        assert notifier.config == config
    
    def test_get_enabled_channels(self):
        """测试获取启用的渠道"""
        config = NotificationConfig(
            dingtalk=DingTalkConfig(enabled=True, webhook="https://example.com"),
            serverchan=ServerChanConfig(enabled=False)
        )
        notifier = NotificationManager(config)
        enabled = notifier.get_enabled_channels()
        assert "dingtalk" in enabled
        assert "serverchan" not in enabled


class TestSQLiteStorageAdapter:
    """存储适配器测试"""
    
    def test_init_db(self, tmp_path):
        """测试数据库初始化"""
        db_path = tmp_path / "test.db"
        storage = SQLiteStorageAdapter(str(db_path))
        assert storage.db_path == str(db_path)
        storage.close()
    
    @pytest.mark.asyncio
    async def test_save_sign_in_result(self, tmp_path):
        """测试保存签到结果"""
        db_path = tmp_path / "test.db"
        storage = SQLiteStorageAdapter(str(db_path))
        
        record = SignInRecord(
            request_id="test-123",
            platform="bilibili",
            account="test_account",
            success=True,
            message="签到成功",
            timestamp=datetime.now()
        )
        
        record_id = await storage.async_save_sign_in_result(record)
        assert record_id > 0
        storage.close()
    
    @pytest.mark.asyncio
    async def test_is_already_signed_today(self, tmp_path):
        """测试检查今日是否已签到"""
        db_path = tmp_path / "test.db"
        storage = SQLiteStorageAdapter(str(db_path))
        
        is_signed = await storage.async_is_already_signed_today(
            platform="bilibili",
            account="test_account"
        )
        assert is_signed is False
        storage.close()


class TestExceptions:
    """异常类测试"""
    
    def test_sign_in_exception(self):
        """测试基础异常"""
        exc = SignInException("测试错误", code=5000)
        assert exc.message == "测试错误"
        assert exc.code == 5000
    
    def test_auth_error(self):
        """测试认证错误"""
        exc = AuthError(platform="bilibili", reason="Cookie过期")
        assert exc.platform == "bilibili"
        assert exc.reason == "Cookie过期"
        assert exc.code == 5201
    
    def test_rate_limit_error(self):
        """测试限流错误"""
        exc = RateLimitError(platform="zhihu", retry_after=60)
        assert exc.platform == "zhihu"
        assert exc.retry_after == 60
        assert exc.code == 5103


class TestModels:
    """数据模型测试"""
    
    def test_sign_in_result(self):
        """测试签到结果"""
        result = SignInResult(
            platform="bilibili",
            account="test",
            success=True,
            message="签到成功"
        )
        assert result.platform == "bilibili"
        assert result.success is True
        assert result.to_dict()["platform"] == "bilibili"
    
    def test_sign_in_task(self):
        """测试签到任务"""
        from autosignin.models.signin import SignInRequest
        
        task = SignInTask(
            task_id="task-123",
            request=SignInRequest(),
            status=TaskStatus.PENDING
        )
        
        task.results.append(SignInResult(success=True))
        task.results.append(SignInResult(success=False))
        
        assert task.success_count == 1
        assert task.failure_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
