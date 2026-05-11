import sqlite3
import json
import time
import os
from typing import Optional, Any
from core.logger import logger

class LocalCache:
    def __init__(self, db_path="nerv_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT value FROM cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    logger.debug(f"Cache HIT para: {key}")
                    return json.loads(row[0])
        except Exception as e:
            logger.error(f"Error leyendo cache: {e}")
        return None

    def set(self, key: str, value: Any):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                    (key, json.dumps(value), time.time())
                )
                conn.commit()
                logger.debug(f"Cache SET para: {key}")
        except Exception as e:
            logger.error(f"Error escribiendo en cache: {e}")

# Instancia global
cache = LocalCache()
