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
)

missing=()
placeholders=()
invalid=()

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

openai_key="$(read_env OPENAI_API_KEY || true)"
if [ -n "$openai_key" ]; then
  case "$openai_key" in
    sk-*) ;;
    *)
      invalid+=("OPENAI_API_KEY must start with sk-. Do not put OPENAI_API_KEY= inside its value.")
      ;;
  esac
fi

telegram_token="$(read_env TELEGRAM_BOT_TOKEN || true)"
if [ -n "$telegram_token" ] && [[ ! "$telegram_token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
  invalid+=("TELEGRAM_BOT_TOKEN has an invalid format. Expected digits:token from BotFather.")
fi

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

if [ "${#invalid[@]}" -gt 0 ]; then
  echo "Invalid values in $env_file:" >&2
  printf '  - %s\n' "${invalid[@]}" >&2
  exit 1
fi

echo "Environment file OK: $env_file"
