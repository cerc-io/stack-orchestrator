FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk bash
RUN curl -L https://unpkg.com/@pnpm/self-installer | node

WORKDIR /app

COPY . .

RUN echo "Installing dependencies..." && \
  pnpm install

# Keep container running for commands to be executed
CMD ["tail", "-f"]
