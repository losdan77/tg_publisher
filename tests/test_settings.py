from app.settings import Settings


def test_admin_telegram_user_ids_parse_csv() -> None:
    settings = Settings(
        openai_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_webhook_secret="dummy",
        admin_telegram_user_ids="1, 2,3",
    )

    assert settings.admin_telegram_user_id_set == {1, 2, 3}

