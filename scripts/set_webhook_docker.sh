#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."
docker compose exec -T tg-publisher python scripts/set_telegram_webhook.py

