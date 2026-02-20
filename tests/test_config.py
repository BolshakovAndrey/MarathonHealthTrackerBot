from unittest.mock import patch
from config.config import Settings


def test_is_production_true():
    with patch.dict("os.environ", {"BOT_TOKEN": "test:token", "APP_ENV": "production"}):
        s = Settings()
        assert s.is_production is True


def test_is_production_false():
    with patch.dict("os.environ", {"BOT_TOKEN": "test:token", "APP_ENV": "development"}):
        s = Settings()
        assert s.is_production is False


def test_use_postgres_true():
    with patch.dict("os.environ", {
        "BOT_TOKEN": "test:token",
        "DATABASE_URL": "postgresql://user:pass@host/db",
    }):
        s = Settings()
        assert s.use_postgres is True


def test_use_postgres_false():
    with patch.dict("os.environ", {"BOT_TOKEN": "test:token"}, clear=False):
        s = Settings(_env_file=None)
        assert s.use_postgres is False


def test_invalid_app_env():
    import pytest
    with pytest.raises(Exception):
        with patch.dict("os.environ", {"BOT_TOKEN": "test:token", "APP_ENV": "unknown"}):
            Settings()
