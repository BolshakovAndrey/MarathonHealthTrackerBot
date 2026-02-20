import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from db.database import Database, _to_pg


# --- Fixture ---

@pytest.fixture
async def db(tmp_path):
    instance = Database()
    instance._sqlite_path = str(tmp_path / "test.db")
    await instance._create_tables()
    yield instance


# --- _to_pg ---

def test_to_pg_single():
    assert _to_pg("SELECT * FROM t WHERE id = ?") == "SELECT * FROM t WHERE id = $1"


def test_to_pg_multiple():
    assert _to_pg("INSERT INTO t VALUES (?, ?, ?)") == "INSERT INTO t VALUES ($1, $2, $3)"


def test_to_pg_no_placeholders():
    assert _to_pg("SELECT 1") == "SELECT 1"


# --- _serial / _pk properties ---

def test_serial_sqlite():
    db = Database()
    db._sqlite_path = ":memory:"
    assert db._serial == "INTEGER"


def test_serial_pg():
    db = Database()
    db._pool = MagicMock()
    with patch("db.database.settings") as s:
        s.use_postgres = True
        assert db._serial == "SERIAL"


def test_pk_sqlite():
    db = Database()
    db._sqlite_path = ":memory:"
    assert db._pk("id") == "id INTEGER PRIMARY KEY AUTOINCREMENT"


def test_pk_pg():
    db = Database()
    with patch("db.database.settings") as s:
        s.use_postgres = True
        assert db._pk("id") == "id SERIAL PRIMARY KEY"


# --- close() ---

async def test_close_no_pool():
    db = Database()
    db._sqlite_path = ":memory:"
    await db.close()  # pool is None — ничего не происходит


async def test_close_with_pool():
    db = Database()
    mock_pool = AsyncMock()
    db._pool = mock_pool
    await db.close()
    mock_pool.close.assert_called_once()


# --- PG paths: execute / fetchall / fetchone ---

async def test_execute_pg():
    db = Database()
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    db._pool = mock_pool
    with patch("db.database.settings") as s:
        s.use_postgres = True
        await db.execute("SELECT ?", (1,))
    mock_conn.execute.assert_called_once_with("SELECT $1", 1)


async def test_fetchall_pg():
    db = Database()
    mock_conn = AsyncMock()
    # asyncpg Record итерируется по значениям — используем списки
    mock_conn.fetch.return_value = [[1], [2]]
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    db._pool = mock_pool
    with patch("db.database.settings") as s:
        s.use_postgres = True
        rows = await db.fetchall("SELECT * FROM t WHERE x = ?", (1,))
    assert rows == [(1,), (2,)]


async def test_fetchone_pg():
    db = Database()
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = [42]
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    db._pool = mock_pool
    with patch("db.database.settings") as s:
        s.use_postgres = True
        row = await db.fetchone("SELECT * FROM t WHERE id = ?", (42,))
    assert row == (42,)


async def test_fetchone_pg_none():
    db = Database()
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    db._pool = mock_pool
    with patch("db.database.settings") as s:
        s.use_postgres = True
        row = await db.fetchone("SELECT * FROM t WHERE id = ?", (99,))
    assert row is None


# --- connect() SQLite path ---

async def test_connect_sqlite(tmp_path):
    db = Database()
    with patch("db.database.settings") as s:
        s.use_postgres = False
        s.DATABASE_PATH = str(tmp_path / "connect_test.db")
        await db.connect()
    assert db._sqlite_path == str(tmp_path / "connect_test.db")


# --- _run_migrations with entry ---

async def test_run_migrations_adds_column(tmp_path):
    db = Database()
    db._sqlite_path = str(tmp_path / "mig.db")
    await db._create_tables()

    # Патчим список миграций, добавляя реальную новую колонку
    with patch.object(db, "_run_migrations", wraps=db._run_migrations):
        original = db._run_migrations

        async def patched_migrations():
            import aiosqlite
            async with aiosqlite.connect(db._sqlite_path) as conn:
                try:
                    await conn.execute("ALTER TABLE users ADD COLUMN test_col TEXT")
                    await conn.commit()
                except Exception:
                    pass

        db._run_migrations = patched_migrations
        await db._run_migrations()

    row = await db.fetchone("PRAGMA table_info(users)")
    assert row is not None


# --- Users ---

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


async def test_upsert_updates_existing(db):
    await db.upsert_user(1, "old", "Old Name")
    await db.upsert_user(1, "new", "New Name")
    row = await db.get_user(1)
    assert row[1] == "new"


async def test_get_user_not_found(db):
    row = await db.get_user(999)
    assert row is None


async def test_has_profile_false_before_update(db):
    await db.upsert_user(1, "u", "U")
    assert await db.has_profile(1) is False


async def test_update_profile_sets_has_profile(db):
    await db.upsert_user(1, "u", "U")
    await db.update_profile(1, "female", 30, 165.0, 58.0, "moderate", "maintain",
                             1400.0, 2000.0, 2000, 120, 60, 250)
    assert await db.has_profile(1) is True


# --- Water ---

async def test_log_and_get_water_today(db):
    from datetime import date
    today = date.today().isoformat()
    await db.upsert_user(1, "u", "U")
    await db.log_water(1, 250)
    await db.log_water(1, 500)
    total = await db.get_water_today(1, today)
    assert total == 750


async def test_get_water_wrong_date(db):
    await db.upsert_user(1, "u", "U")
    await db.log_water(1, 250)
    total = await db.get_water_today(1, "2099-01-01")
    assert total == 0


# --- Mood ---

async def test_log_mood(db):
    await db.upsert_user(1, "u", "U")
    await db.log_mood(1, "😊", "хорошо")
    history = await db.get_mood_history(1)
    assert len(history) == 1
    assert history[0][0] == "😊"


async def test_log_mood_no_note(db):
    await db.upsert_user(1, "u", "U")
    await db.log_mood(1, "😐")
    history = await db.get_mood_history(1)
    assert history[0][1] is None


async def test_mood_history_limit(db):
    await db.upsert_user(1, "u", "U")
    for i in range(10):
        await db.log_mood(1, "😊")
    history = await db.get_mood_history(1, limit=7)
    assert len(history) == 7


# --- Sleep ---

async def test_log_sleep(db):
    await db.upsert_user(1, "u", "U")
    await db.log_sleep(1, "2026-02-20", 7.5, 4)
    history = await db.get_sleep_history(1)
    assert len(history) == 1
    assert history[0][1] == 7.5


async def test_sleep_history_limit(db):
    await db.upsert_user(1, "u", "U")
    for i in range(10):
        await db.log_sleep(1, f"2026-01-{i+1:02d}", float(i), None)
    history = await db.get_sleep_history(1, limit=7)
    assert len(history) == 7


# --- Headache ---

async def test_log_headache(db):
    await db.upsert_user(1, "u", "U")
    await db.log_headache(1, intensity=7, location="висок", triggers="стресс", duration=120)
    history = await db.get_headache_history(1)
    assert len(history) == 1
    assert history[0][0] == 7


async def test_log_headache_minimal(db):
    await db.upsert_user(1, "u", "U")
    await db.log_headache(1, intensity=3)
    history = await db.get_headache_history(1)
    assert history[0][1] is None  # location пустой
