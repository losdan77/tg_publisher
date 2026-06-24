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

read_env() {
  local key="$1"
  local line
  line="$(grep -E "^${key}=" .env | tail -n 1 || true)"
  if [ -z "$line" ]; then
    return 1
  fi

  line="${line#*=}"
  line="${line%$'\r'}"
  line="${line%\"}"
  line="${line#\"}"
  line="${line%\'}"
  line="${line#\'}"
  printf "%s" "$line"
}

bash scripts/check_env.sh .env

mkdir -p data/config data/prompts data/history data/certbot/www data/certbot/conf

if [ ! -f data/config/channels.yaml ]; then
  cp -a config/. data/config/
  echo "Initialized data/config from repository config templates."
fi

if [ ! -f data/prompts/test_ai_news.md ]; then
  cp -a prompts/. data/prompts/
  echo "Initialized data/prompts from repository prompt templates."
fi

app_uid="$(read_env APP_UID || printf "1000")"
app_gid="$(read_env APP_GID || printf "1000")"

if [ "$(id -u)" -eq 0 ]; then
  chown -R "$app_uid:$app_gid" data/config data/prompts data/history
  echo "Set data/config, data/prompts and data/history owner to ${app_uid}:${app_gid}."
else
  if [ ! -w data/config ] || [ ! -w data/prompts ] || [ ! -w data/history ]; then
    echo "data/config, data/prompts or data/history is not writable by the current user." >&2
    echo "Run as root once: chown -R ${app_uid}:${app_gid} data/config data/prompts data/history" >&2
    exit 1
  fi
fi

docker compose config >/dev/null
docker compose up -d --build --remove-orphans
docker image prune -f --filter "until=168h" >/dev/null || true
docker compose ps
