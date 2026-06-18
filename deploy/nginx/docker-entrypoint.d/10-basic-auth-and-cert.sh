#!/bin/sh
set -eu

: "${DOMAIN:?DOMAIN is required}"
: "${NGINX_BASIC_AUTH_USER:?NGINX_BASIC_AUTH_USER is required}"
: "${NGINX_BASIC_AUTH_PASSWORD:?NGINX_BASIC_AUTH_PASSWORD is required}"
: "${ADMIN_API_TOKEN:?ADMIN_API_TOKEN is required}"

mkdir -p /etc/nginx/auth /var/www/certbot "/etc/letsencrypt/live/${DOMAIN}"

htpasswd -bc /etc/nginx/auth/.htpasswd \
  "$NGINX_BASIC_AUTH_USER" \
  "$NGINX_BASIC_AUTH_PASSWORD" >/dev/null

if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ] || \
   [ ! -f "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" ]; then
  openssl req \
    -x509 \
    -nodes \
    -newkey rsa:2048 \
    -days 1 \
    -keyout "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" \
    -out "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" \
    -subj "/CN=${DOMAIN}" >/dev/null 2>&1
fi
