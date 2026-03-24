"""
Cookie 健康检查工具
检测 Cookie 是否有效，提前发现过期问题
"""

import asyncio
import argparse
from typing import Dict, List, Tuple

from autosignin.config import ConfigManager
from autosignin.platforms.manager import PlatformManager


class CookieHealthChecker:
    """Cookie 健康检查器"""

    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self.platform_manager = None

    async def initialize(self):
        """初始化"""
        self.platform_manager = PlatformManager()

        from autosignin.platforms.bilibili import BilibiliPlatform
        from autosignin.platforms.netease import NeteaseMusicPlatform
        from autosignin.platforms.zhihu import ZhihuPlatform
        from autosignin.platforms.juejin import JuejinPlatform
        from autosignin.platforms.v2ex import V2EXPlatform

        self.platform_manager.register("bilibili", BilibiliPlatform)
        self.platform_manager.register("netease_music", NeteaseMusicPlatform)
        self.platform_manager.register("zhihu", ZhihuPlatform)
        self.platform_manager.register("juejin", JuejinPlatform)
        self.platform_manager.register("v2ex", V2EXPlatform)

        await self.platform_manager.initialize_platform("bilibili")
        await self.platform_manager.initialize_platform("netease_music")
        await self.platform_manager.initialize_platform("zhihu")
        await self.platform_manager.initialize_platform("juejin")
        await self.platform_manager.initialize_platform("v2ex")

    async def check_platform_cookies(
        self,
        platform_name: str,
        accounts: List[Dict]
    ) -> List[Dict]:
        """检查单个平台的 Cookie 健康状态"""
        results = []
        platform = self.platform_manager.get_platform(platform_name)

        if not platform:
            return results

        for account in accounts:
            if not account.get("enabled", True):
                continue

            result = {
                "platform": platform_name,
                "account": account.get("name", "unknown"),
                "status": "unknown",
                "message": "",
                "is_valid": False
            }

            cookies = self._extract_cookies(platform_name, account)

            is_valid, error_msg = platform.validate_cookies(cookies)
            if not is_valid:
                result["status"] = "invalid"
                result["message"] = error_msg or "Cookie 格式不完整"
                result["is_valid"] = False
                results.append(result)
                continue

            try:
                verify_result = await platform.verify(cookies)
                if verify_result:
                    result["status"] = "healthy"
                    result["message"] = "Cookie 有效"
                    result["is_valid"] = True
                else:
                    result["status"] = "expired"
                    result["message"] = "Cookie 已过期，请重新获取"
                    result["is_valid"] = False
            except Exception as e:
                result["status"] = "error"
                result["message"] = f"验证失败: {str(e)}"
                result["is_valid"] = False

            results.append(result)

        return results

    def _extract_cookies(self, platform_name: str, account: Dict) -> Dict[str, str]:
        """从账号配置中提取 Cookie"""
        if platform_name == "bilibili":
            return {
                "sessdata": account.get("sessdata", ""),
                "bili_jct": account.get("bili_jct", ""),
                "buvid3": account.get("buvid3", "")
            }
        else:
            return {"cookie": account.get("cookie", "")}

    async def check_all(self) -> Dict:
        """检查所有平台的 Cookie"""
        config_manager = ConfigManager(self.config_path)
        config = config_manager.load()

        all_results = []
        healthy_count = 0
        invalid_count = 0

        accounts_dict = config.accounts.model_dump(exclude_none=True)

        for platform_name, accounts in accounts_dict.items():
            if not accounts:
                continue

            results = await self.check_platform_cookies(platform_name, accounts)
            all_results.extend(results)

            for r in results:
                if r["is_valid"]:
                    healthy_count += 1
                else:
                    invalid_count += 1

        return {
            "results": all_results,
            "total": len(all_results),
            "healthy": healthy_count,
            "invalid": invalid_count,
            "healthy_rate": healthy_count / len(all_results) if all_results else 0
        }


async def cmd_health_check(args) -> int:
    """健康检查命令"""
    print("\n🔍 Cookie 健康检查")
    print("=" * 60)

    checker = CookieHealthChecker(args.config)
    await checker.initialize()

    try:
        result = await checker.check_all()

        for r in result["results"]:
            platform = r["platform"]
            account = r["account"]
            status = r["status"]
            message = r["message"]

            if status == "healthy":
                icon = "✅"
            elif status == "invalid":
                icon = "❌"
            elif status == "expired":
                icon = "⚠️"
            else:
                icon = "❓"

            print(f"\n{icon} {platform}/{account}")
            print(f"   状态: {status}")
            print(f"   信息: {message}")

        print("\n" + "=" * 60)
        print(f"📊 检查结果汇总:")
        print(f"   总计: {result['total']} 个账号")
        print(f"   ✅ 健康: {result['healthy']} 个")
        print(f"   ❌ 异常: {result['invalid']} 个")
        print(f"   健康率: {result['healthy_rate']:.1%}")

        if result["invalid"] > 0:
            print("\n⚠️  有 {0} 个账号存在异常，请及时处理！".format(result["invalid"]))
            return 1

        return 0

    except FileNotFoundError:
        print(f"\n❌ 配置文件不存在: {args.config}")
        print(f"   请先复制 config.example.yml 为 config.yml 并配置账号信息")
        return 1
    except Exception as e:
        print(f"\n❌ 健康检查失败: {e}")
        return 1


def add_health_parser(subparsers):
    """添加 health 命令"""
    health_parser = subparsers.add_parser("health", help="Cookie 健康检查")
    health_parser.add_argument(
        "-p", "--platform",
        help="指定平台检查"
    )
    return health_parser
