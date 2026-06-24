from datetime import datetime, timezone

from app.post_history import PostHistoryStore


def test_post_history_is_persistent_and_isolated_by_channel(tmp_path) -> None:
    database_path = tmp_path / "history" / "posts.sqlite3"
    store = PostHistoryStore(database_path)
    store.add(
        channel_key="first",
        text="Первый пост",
        message_ids=[10],
        reason="schedule",
        published_at=datetime(2026, 6, 24, 8, 0, tzinfo=timezone.utc),
    )
    store.add(
        channel_key="second",
        text="Чужой пост",
        message_ids=[20],
        reason="manual",
    )

    reopened_store = PostHistoryStore(database_path)
    entries = reopened_store.recent("first", limit=10)

    assert [entry.text for entry in entries] == ["Первый пост"]
    assert entries[0].message_ids == (10,)
    assert entries[0].reason == "schedule"


def test_post_history_limit_and_channel_rename(tmp_path) -> None:
    store = PostHistoryStore(tmp_path / "posts.sqlite3")
    for index in range(3):
        store.add("old_key", f"Пост {index}", [index], "manual")

    assert [entry.text for entry in store.recent("old_key", limit=2)] == ["Пост 2", "Пост 1"]

    store.rename_channel("old_key", "new_key")

    assert store.recent("old_key", limit=10) == []
    assert len(store.recent("new_key", limit=10)) == 3
