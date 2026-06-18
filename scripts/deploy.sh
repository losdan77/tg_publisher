#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed on the VPS." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is not installed on the VPS." >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo ".env is missing. The GitHub Action should upload it before deploy." >&2
  exit 1
fi

bash scripts/check_env.sh .env

mkdir -p data/config data/prompts data/certbot/www data/certbot/conf

if [ ! -f data/config/channels.yaml ]; then
  cp -a config/. data/config/
  echo "Initialized data/config from repository config templates."
fi

if [ ! -f data/prompts/test_ai_news.md ]; then
  cp -a prompts/. data/prompts/
  echo "Initialized data/prompts from repository prompt templates."
fi

docker compose config >/dev/null
docker compose up -d --build --remove-orphans
docker image prune -f --filter "until=168h" >/dev/null || true
docker compose ps
