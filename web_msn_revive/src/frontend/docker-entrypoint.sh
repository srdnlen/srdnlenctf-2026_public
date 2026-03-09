#!/bin/sh
set -e

export GATEWAY_HOST=$(echo "$GATEWAY_URL" | sed -E 's|https?://||' | sed 's|/.*||' | sed 's|:.*||')

envsubst '${GATEWAY_URL} ${GATEWAY_HOST}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec nginx -g "daemon off;"
