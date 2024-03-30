from node:20.9.0

# RUN apk --update --no-cache add git make alpine-sdk bash

WORKDIR /app

# Copy the Vega monorepo fork into `/app`
COPY . .

RUN yarn
# RUN ./docker/prepare-dist.sh

