import pytest
import pytest_asyncio
import os

os.environ.setdefault("BOT_TOKEN", "123456:test_token_for_testing_only")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_PATH", ":memory:")
