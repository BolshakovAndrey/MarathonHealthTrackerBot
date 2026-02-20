import pytest
from db.database import Database


@pytest.fixture
async def db(tmp_path):
    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()
    yield instance


async def test_upsert_and_get_user(db):
    await db.upsert_user(123, "testuser", "Test User")
    row = await db.get_user(123)
    assert row is not None
    assert row[0] == 123
    assert row[1] == "testuser"


async def test_has_profile_false_before_update(db):
    await db.upsert_user(1, "u", "U")
    assert await db.has_profile(1) is False


async def test_update_profile_sets_has_profile(db):
    await db.upsert_user(1, "u", "U")
    await db.update_profile(1, "female", 30, 165.0, 58.0, "moderate", "maintain",
                             1400.0, 2000.0, 2000, 120, 60, 250)
    assert await db.has_profile(1) is True


async def test_log_and_get_water(db):
    await db.upsert_user(1, "u", "U")
    await db.log_water(1, 250)
    await db.log_water(1, 500)
    total = await db.get_water_today(1, "2099-01-01")
    assert total == 0  # другая дата — ноль


async def test_log_mood(db):
    await db.upsert_user(1, "u", "U")
    await db.log_mood(1, "😊", "хорошо")
    history = await db.get_mood_history(1)
    assert len(history) == 1
    assert history[0][0] == "😊"


async def test_log_sleep(db):
    await db.upsert_user(1, "u", "U")
    await db.log_sleep(1, "2026-02-20", 7.5, 4)
    history = await db.get_sleep_history(1)
    assert len(history) == 1
    assert history[0][1] == 7.5


async def test_log_headache(db):
    await db.upsert_user(1, "u", "U")
    await db.log_headache(1, intensity=7, location="висок", triggers="стресс", duration=120)
    history = await db.get_headache_history(1)
    assert len(history) == 1
    assert history[0][0] == 7
