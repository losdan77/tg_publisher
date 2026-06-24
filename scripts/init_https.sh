#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo ".env is missing. Create it from .env.example first." >&2
  exit 1
fi

read_env() {
  local key="$1"
  local line
  line="$(grep -E "^${key}=" .env | tail -n 1 || true)"
  line="${line#*=}"
  line="${line%$'\r'}"
  line="${line%\"}"
  line="${line#\"}"
  line="${line%\'}"
  line="${line#\'}"
  printf "%s" "$line"
}

DOMAIN="${DOMAIN:-$(read_env DOMAIN)}"
TELEGRAM_API_PROXY_DOMAIN="${TELEGRAM_API_PROXY_DOMAIN:-$(read_env TELEGRAM_API_PROXY_DOMAIN)}"
TELEGRAM_API_PROXY_DOMAIN="${TELEGRAM_API_PROXY_DOMAIN:-tg-api-test.memeinternet.site}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-$(read_env CERTBOT_EMAIL)}"
CERTBOT_STAGING="${CERTBOT_STAGING:-$(read_env CERTBOT_STAGING)}"
AUTO_SET_TELEGRAM_WEBHOOK="${AUTO_SET_TELEGRAM_WEBHOOK:-$(read_env AUTO_SET_TELEGRAM_WEBHOOK)}"

: "${DOMAIN:?DOMAIN is required in .env}"
: "${TELEGRAM_API_PROXY_DOMAIN:?TELEGRAM_API_PROXY_DOMAIN is required in .env}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL is required in .env}"

mkdir -p data/certbot/www data/certbot/conf

docker compose up -d tg-publisher nginx

staging_arg=""
if [ "${CERTBOT_STAGING:-false}" = "true" ]; then
  staging_arg="--staging"
fi

docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot \
  -w /var/www/certbot \
  --cert-name "$DOMAIN" \
  -d "$DOMAIN" \
  -d "$TELEGRAM_API_PROXY_DOMAIN" \
  --email "$CERTBOT_EMAIL" \
  --agree-tos \
  --no-eff-email \
  --expand \
  --force-renewal \
  $staging_arg

docker compose exec nginx nginx -s reload

echo "HTTPS is ready for https://${DOMAIN} and https://${TELEGRAM_API_PROXY_DOMAIN}"

if [ "${AUTO_SET_TELEGRAM_WEBHOOK:-false}" = "true" ]; then
  docker compose exec -T tg-publisher python scripts/set_telegram_webhook.py
fi
