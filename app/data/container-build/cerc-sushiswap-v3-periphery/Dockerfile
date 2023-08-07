FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk bash

WORKDIR /app

COPY . .

RUN echo "Installing dependencies..." && \
  yarn install

# Keep container running for commands to be executed
CMD ["tail", "-f"]
