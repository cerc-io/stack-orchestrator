FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add git alpine-sdk bash jq
RUN curl -L https://unpkg.com/@pnpm/self-installer | node

WORKDIR /app

COPY . .

RUN echo "Installing dependencies..." && \
  pnpm install
