FROM node:15.3.0-alpine3.10

RUN apk --update --no-cache add make git

WORKDIR /app

COPY . .

RUN echo "Building uniswap-v3-info" && \
    git checkout v0.1.1 && \
    yarn

CMD ["sh", "-c", "yarn start"]
