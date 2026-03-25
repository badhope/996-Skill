"""
Pydantic V2 配置模型
提供配置校验和类型安全
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class CronConfig(BaseModel):
    expression: str = Field(default="0 9 * * *", description="Cron 表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    
    @field_validator('expression')
    @classmethod
    def validate_cron(cls, v: str) -> str:
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {v}")
        return v


class DingTalkConfig(BaseModel):
    enabled: bool = Field(default=False)
    webhook: str = Field(default="")
    secret: str = Field(default="")
    at_mobiles: List[str] = Field(default_factory=list)
    is_at_all: bool = Field(default=False)


class ServerChanConfig(BaseModel):
    enabled: bool = Field(default=False)
    key: str = Field(default="")


class PushPlusConfig(BaseModel):
    enabled: bool = Field(default=False)
    token: str = Field(default="")


class EmailConfig(BaseModel):
    enabled: bool = Field(default=False)
    smtp_server: str = Field(default="smtp.qq.com")
    smtp_port: int = Field(default=587)
    sender: str = Field(default="")
    password: str = Field(default="")
    receiver: str = Field(default="")


class TelegramConfig(BaseModel):
    enabled: bool = Field(default=False)
    bot_token: str = Field(default="")
    chat_id: str = Field(default="")


class NotificationConfig(BaseModel):
    dingtalk: DingTalkConfig = Field(default_factory=DingTalkConfig)
    serverchan: ServerChanConfig = Field(default_factory=ServerChanConfig)
    pushplus: PushPlusConfig = Field(default_factory=PushPlusConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


class BilibiliAccount(BaseModel):
    name: str = Field(default="default")
    sessdata: str = Field(default="")
    bili_jct: str = Field(default="")
    buvid3: str = Field(default="")
    enabled: bool = Field(default=True)


class NeteaseMusicAccount(BaseModel):
    name: str = Field(default="default")
    cookie: str = Field(default="")
    enabled: bool = Field(default=True)


class ZhihuAccount(BaseModel):
    name: str = Field(default="default")
    cookie: str = Field(default="")
    enabled: bool = Field(default=True)


class JuejinAccount(BaseModel):
    name: str = Field(default="default")
    cookie: str = Field(default="")
    enabled: bool = Field(default=True)


class V2EXAccount(BaseModel):
    name: str = Field(default="default")
    cookie: str = Field(default="")
    enabled: bool = Field(default=True)


class AccountsConfig(BaseModel):
    bilibili: List[BilibiliAccount] = Field(default_factory=list)
    netease_music: List[NeteaseMusicAccount] = Field(default_factory=list)
    zhihu: List[ZhihuAccount] = Field(default_factory=list)
    juejin: List[JuejinAccount] = Field(default_factory=list)
    v2ex: List[V2EXAccount] = Field(default_factory=list)


class Config(BaseModel):
    schedule: CronConfig = Field(default_factory=CronConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    accounts: AccountsConfig = Field(default_factory=AccountsConfig)
    
    model_config = {"extra": "allow"}


def load_config_from_yaml(config_path: str) -> Config:
    """从 YAML 文件加载配置"""
    import yaml
    from pathlib import Path
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return Config(**data)


__all__ = [
    "Config",
    "CronConfig",
    "NotificationConfig",
    "AccountsConfig",
    "BilibiliAccount",
    "NeteaseMusicAccount",
    "ZhihuAccount",
    "JuejinAccount",
    "V2EXAccount",
    "DingTalkConfig",
    "ServerChanConfig",
    "PushPlusConfig",
    "EmailConfig",
    "TelegramConfig",
    "load_config_from_yaml",
]
