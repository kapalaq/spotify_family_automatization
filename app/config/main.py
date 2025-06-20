from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.types import SecretStr
from pydantic import Field

import os
from typing import List

HOME_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(HOME_DIR, 'settings', '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )


class TelegramConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix='TG_')

    token: SecretStr
    admin_id: SecretStr


class DatabaseConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix='DB_')

    username: SecretStr
    password: SecretStr
    host: str
    port: int
    database: str


class Config(BaseSettings):
    tg: TelegramConfig = Field(default_factory=TelegramConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)

    @classmethod
    def load(cls) -> 'Config':
        return cls()
