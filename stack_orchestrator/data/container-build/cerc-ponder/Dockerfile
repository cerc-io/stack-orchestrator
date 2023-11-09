FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add git alpine-sdk bash jq curl
RUN curl -L https://unpkg.com/@pnpm/self-installer | node

WORKDIR /app

COPY . .

RUN echo "Installing dependencies and building..." && \
  pnpm install && pnpm build && \
  cd examples/token-erc20 && \
  pnpm install
