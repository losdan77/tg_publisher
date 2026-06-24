import json
import sqlite3
import threading
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


class PostHistoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class PostHistoryEntry:
    channel_key: str
    published_at: str
    text: str
    message_ids: tuple[int, ...]
    reason: str


class PostHistoryStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self._lock = threading.RLock()
        self._initialize()

    def add(
        self,
        channel_key: str,
        text: str,
        message_ids: Sequence[int],
        reason: str,
        published_at: datetime | None = None,
    ) -> None:
        timestamp = (published_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        try:
            with self._lock, closing(self._connect()) as connection, connection:
                connection.execute(
                    """
                    INSERT INTO post_history (channel_key, published_at, text, message_ids, reason)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (channel_key, timestamp, text, json.dumps(list(message_ids)), reason),
                )
        except (OSError, sqlite3.Error) as exc:
            raise PostHistoryError(f"Cannot save post history to {self.database_path}: {exc}") from exc

    def recent(self, channel_key: str, limit: int) -> list[PostHistoryEntry]:
        try:
            with self._lock, closing(self._connect()) as connection, connection:
                rows = connection.execute(
                    """
                    SELECT channel_key, published_at, text, message_ids, reason
                    FROM post_history
                    WHERE channel_key = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (channel_key, limit),
                ).fetchall()
        except (OSError, sqlite3.Error) as exc:
            raise PostHistoryError(f"Cannot read post history from {self.database_path}: {exc}") from exc

        return [
            PostHistoryEntry(
                channel_key=row["channel_key"],
                published_at=row["published_at"],
                text=row["text"],
                message_ids=tuple(json.loads(row["message_ids"])),
                reason=row["reason"],
            )
            for row in rows
        ]

    def rename_channel(self, old_key: str, new_key: str) -> None:
        if old_key == new_key:
            return
        try:
            with self._lock, closing(self._connect()) as connection, connection:
                connection.execute(
                    "UPDATE post_history SET channel_key = ? WHERE channel_key = ?",
                    (new_key, old_key),
                )
        except (OSError, sqlite3.Error) as exc:
            raise PostHistoryError(f"Cannot rename channel history in {self.database_path}: {exc}") from exc

    def _initialize(self) -> None:
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock, closing(self._connect()) as connection, connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS post_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_key TEXT NOT NULL,
                        published_at TEXT NOT NULL,
                        text TEXT NOT NULL,
                        message_ids TEXT NOT NULL,
                        reason TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_post_history_channel
                    ON post_history (channel_key, id DESC)
                    """
                )
        except (OSError, sqlite3.Error) as exc:
            raise PostHistoryError(f"Cannot initialize post history at {self.database_path}: {exc}") from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection
