FROM node:18.15.0-alpine3.16

RUN apk --update --no-cache add make git python3 jq

WORKDIR /app

COPY . .

RUN yarn global add serve

RUN echo "Building react-peer" && \
    yarn install --ignore-scripts && yarn build --ignore @cerc-io/test-app

WORKDIR /app
