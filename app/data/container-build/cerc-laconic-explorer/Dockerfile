# copied and modified from erc20 Dockerfile

FROM node:16.17.1-alpine3.16

RUN apk --update --no-cache add git python3 alpine-sdk

WORKDIR /

COPY . .

RUN echo "Building Laconic Explorer" && \
    git checkout master && \
    yarn

EXPOSE 8080

CMD ["yarn", "serve"]
