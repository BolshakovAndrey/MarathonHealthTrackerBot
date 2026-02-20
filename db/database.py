import re
import logging
import os
import aiosqlite
import asyncpg
from config import settings

logger = logging.getLogger(__name__)


def _to_pg(sql: str) -> str:
    """Конвертирует SQLite-плейсхолдеры ? в PostgreSQL $1, $2, ..."""
    counter = 0

    def replace(_):
        nonlocal counter
        counter += 1
        return f"${counter}"

    return re.sub(r"\?", replace, sql)


class Database:
    def __init__(self):
        self._pool: asyncpg.Pool | None = None
        self._sqlite_path: str | None = None

    @property
    def _use_pg(self) -> bool:
        return settings.use_postgres

    async def connect(self):
        if self._use_pg:
            self._pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=10)
            logger.info("PostgreSQL pool создан")
        else:
            self._sqlite_path = settings.DATABASE_PATH
            db_dir = os.path.dirname(self._sqlite_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            logger.info(f"SQLite: {self._sqlite_path}")

        await self._create_tables()
        await self._run_migrations()

    async def close(self):
        if self._pool:
            await self._pool.close()

    # --- Низкоуровневые методы ---

    async def execute(self, sql: str, params=None):
        params = params or ()
        if self._use_pg:
            async with self._pool.acquire() as conn:
                await conn.execute(_to_pg(sql), *params)
        else:
            async with aiosqlite.connect(self._sqlite_path) as conn:
                await conn.execute("PRAGMA foreign_keys = ON")
                await conn.execute(sql, params)
                await conn.commit()

    async def fetchall(self, sql: str, params=None):
        params = params or ()
        if self._use_pg:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(_to_pg(sql), *params)
                return [tuple(r) for r in rows]
        else:
            async with aiosqlite.connect(self._sqlite_path) as conn:
                await conn.execute("PRAGMA foreign_keys = ON")
                cursor = await conn.execute(sql, params)
                return await cursor.fetchall()

    async def fetchone(self, sql: str, params=None):
        params = params or ()
        if self._use_pg:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(_to_pg(sql), *params)
                return tuple(row) if row else None
        else:
            async with aiosqlite.connect(self._sqlite_path) as conn:
                await conn.execute("PRAGMA foreign_keys = ON")
                cursor = await conn.execute(sql, params)
                return await cursor.fetchone()

    @property
    def _serial(self) -> str:
        """Тип автоинкремента: SERIAL для PG, INTEGER AUTOINCREMENT для SQLite."""
        return "SERIAL" if self._use_pg else "INTEGER"

    def _pk(self, name: str = "id") -> str:
        if self._use_pg:
            return f"{name} SERIAL PRIMARY KEY"
        return f"{name} INTEGER PRIMARY KEY AUTOINCREMENT"

    # --- DDL ---
    # Решение по daily_targets: поля КБЖУ-целей (bmr/tdee/calories/protein/fat/carbs)
    # хранятся в таблице users — у одного пользователя ровно один набор целей,
    # отдельная таблица избыточна на данном этапе.

    async def _create_tables(self):
        # users — профиль пользователя + цели КБЖУ (bmr/tdee/calories/protein/fat/carbs)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id        BIGINT PRIMARY KEY,
                username       TEXT,
                full_name      TEXT,
                gender         TEXT,
                age            INTEGER,
                height         REAL,
                weight         REAL,
                activity_level TEXT,
                goal           TEXT,
                bmr            REAL,
                tdee           REAL,
                calories       INTEGER,
                protein        INTEGER,
                fat            INTEGER,
                carbs          INTEGER,
                created_at     TIMESTAMPTZ DEFAULT NOW(),
                updated_at     TIMESTAMPTZ DEFAULT NOW()
            )
        """ if self._use_pg else """
            CREATE TABLE IF NOT EXISTS users (
                user_id        INTEGER PRIMARY KEY,
                username       TEXT,
                full_name      TEXT,
                gender         TEXT,
                age            INTEGER,
                height         REAL,
                weight         REAL,
                activity_level TEXT,
                goal           TEXT,
                bmr            REAL,
                tdee           REAL,
                calories       INTEGER,
                protein        INTEGER,
                fat            INTEGER,
                carbs          INTEGER,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # water_log — трекинг воды
        await self.execute("""
            CREATE TABLE IF NOT EXISTS water_log (
                id        SERIAL PRIMARY KEY,
                user_id   BIGINT NOT NULL,
                amount_ml INTEGER NOT NULL,
                logged_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """ if self._use_pg else """
            CREATE TABLE IF NOT EXISTS water_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                amount_ml INTEGER NOT NULL,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # mood_log — настроение
        await self.execute("""
            CREATE TABLE IF NOT EXISTS mood_log (
                id        SERIAL PRIMARY KEY,
                user_id   BIGINT NOT NULL,
                emoji     TEXT NOT NULL,
                note      TEXT,
                logged_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """ if self._use_pg else """
            CREATE TABLE IF NOT EXISTS mood_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                emoji     TEXT NOT NULL,
                note      TEXT,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # sleep_log — сон
        await self.execute("""
            CREATE TABLE IF NOT EXISTS sleep_log (
                id         SERIAL PRIMARY KEY,
                user_id    BIGINT NOT NULL,
                sleep_date DATE NOT NULL,
                hours      REAL NOT NULL,
                quality    INTEGER,
                logged_at  TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """ if self._use_pg else """
            CREATE TABLE IF NOT EXISTS sleep_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                sleep_date TEXT NOT NULL,
                hours      REAL NOT NULL,
                quality    INTEGER,
                logged_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # headache_log — мигрени / головные боли
        await self.execute("""
            CREATE TABLE IF NOT EXISTS headache_log (
                id        SERIAL PRIMARY KEY,
                user_id   BIGINT NOT NULL,
                intensity INTEGER NOT NULL,
                location  TEXT,
                triggers  TEXT,
                duration  INTEGER,
                logged_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """ if self._use_pg else """
            CREATE TABLE IF NOT EXISTS headache_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                intensity INTEGER NOT NULL,
                location  TEXT,
                triggers  TEXT,
                duration  INTEGER,
                logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        logger.info("Таблицы созданы / проверены")

    async def _run_migrations(self):
        migrations = [
            ("users", "water_goal_ml", "INTEGER"),
        ]
        for table, column, col_type in migrations:
            try:
                await self.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            except Exception:
                pass

    # --- Users ---

    async def upsert_user(self, user_id: int, username: str, full_name: str):
        await self.execute(
            """INSERT INTO users (user_id, username, full_name)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username  = excluded.username,
                 full_name = excluded.full_name,
                 updated_at = CURRENT_TIMESTAMP""",
            (user_id, username, full_name),
        )

    async def get_user(self, user_id: int):
        return await self.fetchone(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )

    async def update_profile(
        self, user_id: int, gender: str, age: int, height: float, weight: float,
        activity_level: str, goal: str, bmr: float, tdee: float,
        calories: int, protein: int, fat: int, carbs: int,
    ):
        await self.execute(
            """UPDATE users SET
               gender = ?, age = ?, height = ?, weight = ?,
               activity_level = ?, goal = ?,
               bmr = ?, tdee = ?, calories = ?, protein = ?, fat = ?, carbs = ?,
               updated_at = CURRENT_TIMESTAMP
               WHERE user_id = ?""",
            (gender, age, height, weight, activity_level, goal,
             bmr, tdee, calories, protein, fat, carbs, user_id),
        )

    async def has_profile(self, user_id: int) -> bool:
        row = await self.fetchone(
            "SELECT 1 FROM users WHERE user_id = ? AND gender IS NOT NULL", (user_id,)
        )
        return row is not None

    # --- Water ---

    async def log_water(self, user_id: int, amount_ml: int):
        await self.execute(
            "INSERT INTO water_log (user_id, amount_ml) VALUES (?, ?)",
            (user_id, amount_ml),
        )

    async def get_water_today(self, user_id: int, today: str) -> int:
        row = await self.fetchone(
            "SELECT COALESCE(SUM(amount_ml), 0) FROM water_log WHERE user_id = ? AND DATE(logged_at) = ?",
            (user_id, today),
        )
        return row[0] if row else 0

    async def get_water_week(self, user_id: int, dates: list[str]) -> dict[str, int]:
        """Возвращает {date: total_ml} за переданные даты."""
        result = {d: 0 for d in dates}
        rows = await self.fetchall(
            "SELECT DATE(logged_at), COALESCE(SUM(amount_ml), 0) FROM water_log "
            "WHERE user_id = ? AND DATE(logged_at) >= ? AND DATE(logged_at) <= ? "
            "GROUP BY DATE(logged_at)",
            (user_id, dates[0], dates[-1]),
        )
        for raw_date, total in rows:
            # PG возвращает date-объект, SQLite — строку
            date_str = raw_date.isoformat() if hasattr(raw_date, "isoformat") else str(raw_date)
            if date_str in result:
                result[date_str] = total
        return result

    async def set_water_goal(self, user_id: int, goal_ml: int):
        # upsert гарантирует наличие строки перед UPDATE
        await self.execute(
            """INSERT INTO users (user_id, water_goal_ml)
               VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET water_goal_ml = excluded.water_goal_ml""",
            (user_id, goal_ml),
        )

    async def get_water_goal(self, user_id: int) -> int | None:
        row = await self.fetchone(
            "SELECT water_goal_ml FROM users WHERE user_id = ?", (user_id,)
        )
        return row[0] if row else None

    # --- Mood ---

    async def log_mood(self, user_id: int, emoji: str, note: str = None):
        await self.execute(
            "INSERT INTO mood_log (user_id, emoji, note) VALUES (?, ?, ?)",
            (user_id, emoji, note),
        )

    async def get_mood_history(self, user_id: int, limit: int = 7):
        return await self.fetchall(
            "SELECT emoji, note, logged_at FROM mood_log WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        )

    # --- Sleep ---

    async def log_sleep(self, user_id: int, sleep_date: str, hours: float, quality: int = None):
        await self.execute(
            """INSERT INTO sleep_log (user_id, sleep_date, hours, quality)
               VALUES (?, ?, ?, ?)
               ON CONFLICT DO NOTHING""",
            (user_id, sleep_date, hours, quality),
        )

    async def get_sleep_history(self, user_id: int, limit: int = 7):
        return await self.fetchall(
            "SELECT sleep_date, hours, quality FROM sleep_log WHERE user_id = ? ORDER BY sleep_date DESC LIMIT ?",
            (user_id, limit),
        )

    # --- Headache ---

    async def log_headache(
        self, user_id: int, intensity: int,
        location: str = None, triggers: str = None, duration: int = None,
    ):
        await self.execute(
            "INSERT INTO headache_log (user_id, intensity, location, triggers, duration) VALUES (?, ?, ?, ?, ?)",
            (user_id, intensity, location, triggers, duration),
        )

    async def get_headache_history(self, user_id: int, limit: int = 10):
        return await self.fetchall(
            "SELECT intensity, location, triggers, duration, logged_at FROM headache_log WHERE user_id = ? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        )


db = Database()
