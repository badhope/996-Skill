# 🔄 Auto-SignIn

一个强大的多平台自动签到系统，支持哔哩哔哩、网易云音乐、知乎、掘金等主流平台。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

## ✨ 功能特性

- 🎯 **多平台支持** - 哔哩哔哩、网易云音乐、知乎、掘金、V2EX等
- ⏰ **定时任务** - 支持 Cron 表达式灵活配置
- 🐳 **Docker 支持** - 一键部署，开箱即用
- 📱 **多账号管理** - 支持多账号同时签到
- 🔔 **通知推送** - 支持钉钉、微信、邮件等多种通知方式
- 📝 **日志记录** - 完整的签到日志和错误追踪

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/badhope/Auto-SignIn.git
cd Auto-SignIn

# 复制配置文件
cp config.example.yml config.yml

# 编辑配置文件，添加你的账号信息
vim config.yml

# 启动
docker-compose up -d
```

### 方式二：本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 📁 项目结构

```
Auto-SignIn/
├── 📄 main.py              # 主程序入口
├── 📄 config.yml           # 配置文件
├── 📁 core/                # 核心模块
│   ├── __init__.py
│   ├── scheduler.py        # 定时任务
│   ├── notifier.py         # 通知模块
│   └── logger.py           # 日志模块
├── 📁 platforms/           # 平台签到实现
│   ├── __init__.py
│   ├── bilibili.py         # 哔哩哔哩
│   ├── netease_music.py    # 网易云音乐
│   ├── zhihu.py            # 知乎
│   ├── juejin.py           # 掘金
│   └── v2ex.py             # V2EX
├── 📁 utils/               # 工具函数
│   ├── __init__.py
│   ├── http.py             # HTTP请求
│   └── crypto.py           # 加密工具
├── 📁 tests/               # 测试
├── 📄 Dockerfile           # Docker配置
├── 📄 docker-compose.yml   # Docker Compose
├── 📄 requirements.txt     # Python依赖
└── 📄 README.md            # 本文件
```

## ⚙️ 配置说明

编辑 `config.yml`：

```yaml
# 定时任务配置
schedule:
  # 每天上午9点执行
  cron: "0 9 * * *"
  # 或每小时执行一次
  # cron: "0 * * * *"

# 通知配置
notifications:
  # 钉钉
  dingtalk:
    enabled: false
    webhook: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: "xxx"
  
  # Server酱
  serverchan:
    enabled: false
    key: "xxx"
  
  # 邮箱
  email:
    enabled: false
    smtp_server: "smtp.qq.com"
    smtp_port: 587
    sender: "your@email.com"
    password: "xxx"
    receiver: "receiver@email.com"

# 平台账号配置
accounts:
  bilibili:
    - name: "账号1"
      sessdata: "xxx"
      bili_jct: "xxx"
      buvid3: "xxx"
  
  netease_music:
    - name: "账号1"
      cookie: "xxx"
  
  zhihu:
    - name: "账号1"
      cookie: "xxx"
  
  juejin:
    - name: "账号1"
      cookie: "xxx"
```

## 🔑 获取 Cookie 方法

### 哔哩哔哩
1. 登录 https://www.bilibili.com
2. F12 打开开发者工具 → Application → Cookies
3. 复制 `SESSDATA`, `bili_jct`, `buvid3`

### 网易云音乐
1. 登录 https://music.163.com
2. F12 → Application → Cookies → music.163.com
3. 复制完整的 Cookie 字符串

### 其他平台
类似方法，登录后从开发者工具获取 Cookie。

## 🛠️ 开发指南

### 添加新平台

1. 在 `platforms/` 目录创建新的平台文件
2. 继承 `BasePlatform` 类
3. 实现 `sign_in()` 方法

```python
# platforms/example.py
from .base import BasePlatform

class ExamplePlatform(BasePlatform):
    name = "example"
    base_url = "https://example.com"
    
    async def sign_in(self, account: dict) -> dict:
        # 实现签到逻辑
        response = await self.http.post("/sign")
        return {
            "success": response.status == 200,
            "message": "签到成功" if response.status == 200 else "签到失败"
        }
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定平台测试
pytest tests/test_bilibili.py

# 带覆盖率报告
pytest --cov=core --cov=platforms
```

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 🤝 贡献指南

欢迎提交 Issue 和 PR！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

[MIT License](LICENSE)

## ⚠️ 免责声明

本工具仅供学习交流使用，请勿用于商业用途。使用本工具时请遵守相关平台的服务条款。

---

⭐ 如果这个项目对你有帮助，请点个 Star 支持一下！
