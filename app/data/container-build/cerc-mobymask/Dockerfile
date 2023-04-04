FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add python3 alpine-sdk jq bash

WORKDIR /app

COPY . .

RUN yarn

# Add scripts
RUN mkdir /scripts
ENV PATH="${PATH}:/scripts"
