from app.telegram_client import split_telegram_text


def test_split_telegram_text_keeps_short_text_as_single_chunk() -> None:
    assert split_telegram_text("hello") == ["hello"]


def test_split_telegram_text_splits_long_text() -> None:
    text = "word " * 2000
    chunks = split_telegram_text(text, limit=100)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_split_telegram_text_splits_long_word() -> None:
    chunks = split_telegram_text("x" * 250, limit=100)

    assert [len(chunk) for chunk in chunks] == [100, 100, 50]
