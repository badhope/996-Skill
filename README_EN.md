# Auto-SignIn

一个强大的多平台自动签到系统，支持哔哩哔哩、网易云音乐、知乎、掘金、V2EX 等主流平台。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![GitHub stars](https://img.shields.io/github/stars/badhope/Auto-SignIn)](https://github.com/badhope/Auto-SignIn/stargazers)

[中文](./README.md) | [English](./README_EN.md)

## 功能特性

- **多平台支持** - 哔哩哔哩、网易云音乐、知乎、掘金、V2EX
- **定时任务** - 支持 Cron 表达式灵活配置
- **Docker 支持** - 一键部署，开箱即用
- **多账号管理** - 支持多账号同时签到
- **多渠道通知** - 钉钉、Server酱、PushPlus、邮件、Telegram
- **完整日志** - 完整的签到日志和错误追踪
- **容错机制** - 重试、熔断、限流、舱壁隔离
- **插件架构** - 轻松扩展新平台

## 支持的平台

| 平台 | 显示名 | 状态 |
|------|--------|------|
| bilibili | 哔哩哔哩 | ✅ |
| netease_music | 网易云音乐 | ✅ |
| zhihu | 知乎 | ✅ |
| juejin | 掘金 | ✅ |
| v2ex | V2EX | ✅ |

## 快速开始

### Docker 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/badhope/Auto-SignIn.git
cd Auto-SignIn

# 复制配置文件
cp config.example.yml config.yml

# 编辑配置文件，添加你的账号信息
vim config.yml

# 启动服务
docker-compose up -d
```

### 本地运行

```bash
# 克隆仓库
git clone https://github.com/badhope/Auto-SignIn.git
cd Auto-SignIn

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 执行签到
python main.py sign

# 启动调度器
python main.py run
```

## 项目结构

```
Auto-SignIn/
├── autosignin/              # 主包
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py               # 命令行界面
│   ├── config/              # 配置模块
│   │   ├── __init__.py
│   │   ├── config.py        # ConfigManager
│   │   └── models.py        # Pydantic 模型
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── engine.py        # SignInEngine
│   │   ├── exceptions.py     # 异常类
│   │   ├── notifier.py      # NotificationManager
│   │   ├── scheduler.py     # TaskScheduler
│   │   └── storage.py       # StorageAdapter
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── account.py       # 账号模型
│   │   └── signin.py        # 签到模型
│   ├── platforms/           # 平台插件
│   │   ├── __init__.py
│   │   ├── base.py          # BasePlatform
│   │   ├── manager.py       # PlatformManager
│   │   ├── bilibili.py      # 哔哩哔哩插件
│   │   ├── netease.py       # 网易云音乐插件
│   │   ├── zhihu.py         # 知乎插件
│   │   ├── juejin.py        # 掘金插件
│   │   └── v2ex.py          # V2EX 插件
│   ├── resilience/          # 容错模式
│   │   ├── __init__.py
│   │   ├── retry.py         # 指数退避重试
│   │   ├── circuit_breaker.py  # 熔断器
│   │   ├── rate_limiter.py    # 限流器
│   │   └── bulkhead.py        # 舱壁隔离
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── logging_config.py   # 日志配置
├── docs/                    # 文档
├── tests/                   # 测试
├── main.py                  # 入口文件
├── config.example.yml        # 配置示例
├── requirements.txt          # Python 依赖
├── Dockerfile
└── docker-compose.yml
```

## 命令行使用

```bash
# 显示帮助
python main.py --help

# 列出所有平台
python main.py list

# 显示系统状态
python main.py status

# 执行签到
python main.py sign

# 指定平台签到
python main.py sign -p bilibili zhihu

# 使用指定配置文件
python main.py -c config.yml sign

# 启动调度器
python main.py run
```

## 配置说明

编辑 `config.yml`:

```yaml
# 定时任务配置
schedule:
  # 每天上午9点执行
  cron: "0 9 * * *"
  timezone: "Asia/Shanghai"

# 通知配置
notifications:
  dingtalk:
    enabled: false
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: "xxx"

  serverchan:
    enabled: false
    key: "xxx"

  pushplus:
    enabled: false
    token: "xxx"

  email:
    enabled: false
    smtp_server: "smtp.qq.com"
    smtp_port: 587
    sender: "your@email.com"
    password: "xxx"
    receiver: "receiver@email.com"

  telegram:
    enabled: false
    bot_token: "xxx"
    chat_id: "xxx"

# 账号配置
accounts:
  bilibili:
    - name: "账号1"
      sessdata: "xxx"
      bili_jct: "xxx"
      buvid3: "xxx"
      enabled: true

  netease_music:
    - name: "账号1"
      cookie: "xxx"
      enabled: true

  zhihu:
    - name: "账号1"
      cookie: "xxx"
      enabled: true

  juejin:
    - name: "账号1"
      cookie: "xxx"
      enabled: true

  v2ex:
    - name: "账号1"
      cookie: "xxx"
      enabled: true
```

## 如何获取 Cookie

### 哔哩哔哩
1. 登录 https://www.bilibili.com
2. 按 F12 → Application → Cookies
3. 复制 `SESSDATA`、`bili_jct`、`buvid3`

### 网易云音乐
1. 登录 https://music.163.com
2. 按 F12 → Application → Cookies
3. 复制完整的 Cookie 字符串

### 其他平台
类似步骤，登录后从开发者工具获取 Cookie。

## 添加新平台

1. 在 `autosignin/platforms/` 目录创建新的平台文件
2. 继承 `BasePlatform`
3. 使用 `@register_platform` 装饰器
4. 实现 `sign_in()` 方法

```python
from autosignin.platforms.base import BasePlatform, register_platform
from autosignin.models.signin import SignInResult

@register_platform(
    name="example",
    display_name="示例平台",
    version="1.0.0",
    capabilities=["daily_sign"],
    required_fields=["cookie"]
)
class ExamplePlatform(BasePlatform):
    name = "example"
    display_name = "示例平台"
    base_url = "https://api.example.com"

    async def sign_in(self, account_name: str, cookies: dict) -> SignInResult:
        result = SignInResult(
            platform=self.name,
            account=account_name
        )
        # 实现签到逻辑
        return result
```

## 架构设计

```
┌─────────────────────────────────────────────────┐
│                   SignInEngine                   │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │   Platform  │  │   Storage  │  │Notifier │  │
│  │   Manager   │  │  Adapter   │  │ Manager │  │
│  └──────┬──────┘  └──────┬──────┘  └────┬────┘  │
│         │                │              │       │
│  ┌──────┴──────┐  ┌──────┴──────┐       │       │
│  │   Platform  │  │    SQLite  │       │       │
│  │   Plugins   │  │   Storage  │       │       │
│  └─────────────┘  └─────────────┘       │       │
│                                          │       │
│  ┌──────────────────────────────────────┐│       │
│  │           Resilience Layer            ││       │
│  │  ┌──────┐ ┌──────────┐ ┌──────────┐ ││       │
│  │  │Retry │ │Circuit   │ │Rate      │ ││       │
│  │  │      │ │Breaker   │ │Limiter   │ ││       │
│  │  └──────┘ └──────────┘ └──────────┘ ││       │
│  └──────────────────────────────────────┘│       │
└─────────────────────────────────────────────────┘
```

## 测试

```bash
# 运行所有测试
pytest

# 运行特定平台测试
pytest tests/test_bilibili.py

# 带覆盖率报告
pytest --cov=autosignin --cov-report=html
```

## 文档

详细文档见 [docs/](docs/)：
- [问题分析与解决方案](docs/problems_and_solutions.md)
- [后续工作计划](docs/next_steps.md)

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 贡献指南

欢迎提交 Issue 和 PR！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

[MIT License](LICENSE)

## 免责声明

本工具仅供学习交流使用，请勿用于商业用途。使用本工具时请遵守相关平台的服务条款。
