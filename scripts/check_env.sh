#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

env_file="${1:-.env}"

if [ ! -f "$env_file" ]; then
  echo "$env_file is missing." >&2
  exit 1
fi

read_env() {
  local key="$1"
  local line
  line="$(grep -E "^${key}=" "$env_file" | tail -n 1 || true)"
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

required_vars=(
  DOMAIN
  PUBLIC_BASE_URL
  CERTBOT_EMAIL
  NGINX_BASIC_AUTH_USER
  NGINX_BASIC_AUTH_PASSWORD
  ADMIN_API_TOKEN
  OPENAI_API_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_WEBHOOK_SECRET
  CHANNELS_CONFIG_PATH
)

missing=()
placeholders=()

for key in "${required_vars[@]}"; do
  value="$(read_env "$key" || true)"
  if [ -z "$value" ]; then
    missing+=("$key")
    continue
  fi

  case "$value" in
    change-this*|sk-your-*|*your-telegram-bot-token*|you@example.com)
      placeholders+=("$key")
      ;;
  esac
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing required variables in $env_file:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  exit 1
fi

if [ "${#placeholders[@]}" -gt 0 ]; then
  echo "Placeholder values are still present in $env_file:" >&2
  printf '  - %s\n' "${placeholders[@]}" >&2
  echo "Replace them with real secrets before deploy." >&2
  exit 1
fi

echo "Environment file OK: $env_file"

