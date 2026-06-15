FROM nginx:1.27-alpine

RUN apk add --no-cache apache2-utils openssl

COPY templates/default.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.d/10-basic-auth-and-cert.sh /docker-entrypoint.d/10-basic-auth-and-cert.sh

RUN chmod +x /docker-entrypoint.d/10-basic-auth-and-cert.sh

