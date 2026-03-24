"""
命令行界面
"""

import asyncio
import argparse
import sys
from typing import Optional

from autosignin import __version__
from autosignin.config import ConfigManager
from autosignin.core.engine import SignInEngine
from autosignin.core.notifier import NotificationManager
from autosignin.core.scheduler import TaskScheduler
from autosignin.core.storage import SQLiteStorageAdapter
from autosignin.platforms.manager import PlatformManager
from autosignin.utils.logging_config import setup_logging, get_logger
from autosignin.core.health import cmd_health_check, add_health_parser


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="autosignin",
        description="Auto-SignIn 多平台自动签到系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="config.yml",
        help="配置文件路径 (默认: config.yml)"
    )
    
    parser.add_argument(
        "-l", "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    sign_parser = subparsers.add_parser("sign", help="执行签到")
    sign_parser.add_argument(
        "-p", "--platform",
        nargs="+",
        help="指定平台 (默认全部)"
    )
    sign_parser.add_argument(
        "-a", "--account",
        nargs="+",
        help="指定账号 (默认全部)"
    )
    sign_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="强制签到 (跳过重复检查)"
    )
    
    list_parser = subparsers.add_parser("list", help="列出平台")
    list_parser.add_argument(
        "--enabled-only",
        action="store_true",
        help="仅显示已启用的平台"
    )
    
    subparsers.add_parser("status", help="显示状态")
    
    run_parser = subparsers.add_parser("run", help="运行调度器")
    run_parser.add_argument(
        "--daemon",
        action="store_true",
        help="后台运行"
    )

    add_health_parser(subparsers)

    return parser


async def init_engine(config_path: str) -> SignInEngine:
    """初始化签到引擎"""
    config_manager = ConfigManager(config_path)
    config = config_manager.load()
    
    setup_logging(level="INFO")
    logger = get_logger("autosignin")
    
    platform_manager = PlatformManager()
    
    from autosignin.platforms.bilibili import BilibiliPlatform
    from autosignin.platforms.netease import NeteaseMusicPlatform
    from autosignin.platforms.zhihu import ZhihuPlatform
    from autosignin.platforms.juejin import JuejinPlatform
    from autosignin.platforms.v2ex import V2EXPlatform

    platform_manager.register("bilibili", BilibiliPlatform)
    platform_manager.register("netease_music", NeteaseMusicPlatform)
    platform_manager.register("zhihu", ZhihuPlatform)
    platform_manager.register("juejin", JuejinPlatform)
    platform_manager.register("v2ex", V2EXPlatform)

    await platform_manager.initialize_platform("bilibili")
    await platform_manager.initialize_platform("netease_music")
    await platform_manager.initialize_platform("zhihu")
    await platform_manager.initialize_platform("juejin")
    await platform_manager.initialize_platform("v2ex")
    
    storage = SQLiteStorageAdapter("data/signin.db")
    
    notifier = NotificationManager(config.notifications)
    
    scheduler = TaskScheduler()
    
    engine = SignInEngine(
        platform_manager=platform_manager,
        storage=storage,
        notifier=notifier,
        scheduler=scheduler,
        max_concurrent=5
    )
    engine.set_config(config)
    
    return engine


async def cmd_sign(args) -> int:
    """执行签到命令"""
    engine = await init_engine(args.config)
    logger = get_logger("autosignin")
    
    platforms = args.platform or []
    accounts = args.account or []
    force = args.force or False
    
    from autosignin.models.signin import SignInRequest
    
    request = SignInRequest(
        platforms=platforms,
        accounts=accounts,
        force=force
    )
    
    logger.info(f"Starting sign-in: platforms={platforms}, accounts={accounts}, force={force}")
    
    task = await engine.execute_sign_in_batch(request)
    
    logger.info(f"Sign-in completed: success={task.success_count}, failed={task.failure_count}")
    
    for result in task.results:
        status = "✅" if result.success else "❌"
        logger.info(f"{status} {result.platform}/{result.account}: {result.message}")
    
    await engine.notifier.send_summary(task.results)
    
    storage: SQLiteStorageAdapter = engine.storage
    storage.close()
    
    return 0 if task.failure_count == 0 else 1


async def cmd_list(args) -> int:
    """列出平台命令"""
    engine = await init_engine(args.config)
    
    platforms = engine.platform_manager.list_platforms()
    
    print("\n可用平台:")
    print("-" * 60)
    print(f"{'名称':<20} {'显示名':<20} {'版本':<10} {'状态':<10}")
    print("-" * 60)
    
    for p in platforms:
        status = "✅ 就绪" if p.get("status") == "ready" else f"❌ {p.get('status')}"
        print(f"{p.get('name'):<20} {p.get('display_name'):<20} {p.get('version'):<10} {status:<10}")
    
    print("-" * 60)
    
    storage: SQLiteStorageAdapter = engine.storage
    storage.close()
    
    return 0


async def cmd_status(args) -> int:
    """显示状态命令"""
    print("\nAuto-SignIn 系统状态")
    print("=" * 60)
    print(f"版本: {__version__}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    
    return 0


async def cmd_run(args) -> int:
    """运行调度器命令"""
    engine = await init_engine(args.config)
    logger = get_logger("autosignin")
    
    logger.info("Starting scheduler...")
    
    scheduler = engine.scheduler
    scheduler.register_handler("sign_in", engine.execute_sign_in_batch)
    
    from autosignin.config import load_config_from_yaml
    config = load_config_from_yaml(args.config)
    
    scheduler.add_cron_job(
        job_id="daily_sign_in",
        handler_name="sign_in",
        cron_expression=config.schedule.expression,
        timezone=config.schedule.timezone,
        name="每日签到"
    )
    
    scheduler.start()

    logger.info(f"Scheduler started. Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await engine.graceful_shutdown(timeout_seconds=30)

    return 0


async def main() -> int:
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "sign": cmd_sign,
        "list": cmd_list,
        "status": cmd_status,
        "run": cmd_run,
        "health": cmd_health_check
    }

    if args.command in commands:
        return await commands[args.command](args)
    
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
