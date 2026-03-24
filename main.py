#!/usr/bin/env python3
"""
Auto-SignIn 多平台自动签到系统

用法:
    python main.py sign              # 执行签到
    python main.py list             # 列出平台
    python main.py status           # 显示状态
    python main.py run              # 启动调度器
    python main.py -c config.yml sign  # 使用指定配置
"""

import sys
import asyncio

sys.path.insert(0, ".")

from autosignin.cli import main

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
