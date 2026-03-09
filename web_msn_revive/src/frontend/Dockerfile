FROM node:22-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm@latest

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm build


FROM nginx:alpine

RUN apk add --no-cache gettext

RUN addgroup --system app && adduser --system -G app app

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf.template

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

RUN chown -R app:app /usr/share/nginx/html && \
    chown -R app:app /var/cache/nginx && \
    chown -R app:app /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R app:app /var/run/nginx.pid && \
    touch /etc/nginx/nginx.conf && \
    chown app:app /etc/nginx/nginx.conf && \
    chown app:app /etc/nginx/nginx.conf.template

USER app

EXPOSE 8080

CMD ["/docker-entrypoint.sh"]
