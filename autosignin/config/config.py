"""
配置管理模块
"""

from autosignin.config.models import (
    Config,
    CronConfig,
    NotificationConfig,
    AccountsConfig,
    BilibiliAccount,
    NeteaseMusicAccount,
    ZhihuAccount,
    JuejinAccount,
    V2EXAccount,
    DingTalkConfig,
    ServerChanConfig,
    PushPlusConfig,
    EmailConfig,
    TelegramConfig,
    load_config_from_yaml
)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self._config: Config = None
    
    def load(self) -> Config:
        """加载配置"""
        import yaml
        from pathlib import Path
        
        path = Path(self.config_path)
        if not path.exists():
            path = Path("config.example.yml")
        
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._config = Config(**data)
        else:
            self._config = Config()
        
        return self._config
    
    def save(self, config: Config = None):
        """保存配置"""
        import yaml
        
        config = config or self._config
        if config is None:
            return
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(), f, allow_unicode=True)
    
    @property
    def config(self) -> Config:
        return self._config


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
    "ConfigManager",
]
