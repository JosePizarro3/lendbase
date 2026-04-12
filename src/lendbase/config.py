from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class BaseConfig:
    app_name: str = "lendbase"
    secret_key: str = os.getenv("LENDBASE_SECRET_KEY", "dev-only-change-me")
    database_url: str = os.getenv("LENDBASE_DATABASE_URL", "sqlite:///instance/lendbase-dev.db")
    app_base_url: str = os.getenv("LENDBASE_APP_BASE_URL", "http://127.0.0.1:5000")
    session_cookie_secure: bool = False
    testing: bool = False

    def as_flask_config(self) -> dict[str, object]:
        return {
            "APP_NAME": self.app_name,
            "ENVIRONMENT_NAME": self.environment_name,
            "SECRET_KEY": self.secret_key,
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "APP_BASE_URL": self.app_base_url.rstrip("/"),
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_SECURE": self.session_cookie_secure,
            "TESTING": self.testing,
        }


@dataclass(slots=True)
class DevelopmentConfig(BaseConfig):
    environment_name: str = "development"


@dataclass(slots=True)
class TestingConfig(BaseConfig):
    environment_name: str = "testing"
    secret_key: str = "test-secret-key"
    database_url: str = "sqlite:///:memory:"
    app_base_url: str = "http://localhost"
    testing: bool = True


@dataclass(slots=True)
class ProductionConfig(BaseConfig):
    environment_name: str = "production"
    session_cookie_secure: bool = True


def get_config() -> BaseConfig:
    env_name = os.getenv("LENDBASE_ENV", "development").lower()
    configs: dict[str, type[BaseConfig]] = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    config_class = configs.get(env_name)
    if config_class is None:
        valid = ", ".join(sorted(configs))
        raise ValueError(f"Unsupported LENDBASE_ENV '{env_name}'. Expected one of: {valid}.")
    return config_class()
