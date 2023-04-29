FROM node:16.17.1-alpine3.16 AS build-env

# install dependencies
ENV PACKAGES add git python3 alpine-sdk
RUN apk --update --no-cache $PACKAGES

# copy source files
RUN mkdir /root/laconic-explorer
WORKDIR /root/laconic-explorer
COPY . .

# build
RUN yarn && yarn build

#########################################

# final image
FROM nginx:alpine

# copy files from build stage
COPY --from=build-env /root/laconic-explorer/ping.conf /etc/nginx/conf.d/default.conf
COPY --from=build-env /root/laconic-explorer/dist   /usr/share/nginx/html
