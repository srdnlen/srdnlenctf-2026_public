FROM node:20-alpine

RUN addgroup --system app && adduser --system -G app app

WORKDIR /app

RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --prod --frozen-lockfile

COPY gateway.js .

ENV NODE_ENV=production \
    PORT=8080 \
    BACKEND_HOST=backend \
    BACKEND_PORT=5000

USER app

EXPOSE 8080

CMD ["node", "gateway.js"]