FROM golang:1.21-bullseye AS builder

# Copy files into image
WORKDIR /app
COPY . .

# Build the binary
RUN go build -v -o nitro .

# Reduce image size
FROM node:18-bullseye-slim as builder-ui
RUN apt-get update
RUN apt-get install -y make
WORKDIR /app
COPY . .
RUN yarn
RUN VITE_RPC_HOST=CERC_RUNTIME_ENV_RPC_HOST make ui/build

FROM node:18-bullseye-slim
RUN apt-get update
RUN apt-get install -y ca-certificates jq netcat make
RUN rm -rf /var/lib/apt/lists/*
RUN npm install -g http-server
WORKDIR /app
COPY --from=builder /app/nitro .
COPY --from=builder-ui /app/packages/nitro-gui/dist /app/ui
