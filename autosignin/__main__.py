"""
Auto-SignIn 包入口
"""

import sys
import asyncio

from autosignin.cli import main

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
