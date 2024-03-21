FROM golang:1.21-bullseye AS builder

# Copy files into image
WORKDIR /app
COPY . .

# Build the binary
RUN go build -v -o nitro .

# Reduce image size
FROM node:18-bullseye-slim as builder-node
RUN apt-get update
RUN apt-get install -y make
WORKDIR /app
COPY . .
RUN find . -name 'node_modules' | xargs -n1 rm -rf
RUN find . -name 'dist' | xargs -n1 rm -rf
RUN yarn
WORKDIR /app/packages/nitro-gui
RUN VITE_RPC_URL=CERC_RUNTIME_ENV_RPC_URL VITE_TARGET_URL=CERC_RUNTIME_ENV_TARGET_URL yarn build
WORKDIR /app/packages/nitro-auth-gui
RUN VITE_RPC_URL=CERC_RUNTIME_ENV_RPC_URL VITE_TARGET_URL=CERC_RUNTIME_ENV_TARGET_URL yarn build
WORKDIR /app/packages/nitro-auth
RUN yarn build

FROM node:18-bullseye-slim
RUN apt-get update
RUN apt-get install -y ca-certificates jq netcat make
RUN rm -rf /var/lib/apt/lists/*
RUN npm install -g http-server
WORKDIR /app
COPY --from=builder /app/nitro .
COPY --from=builder-node /app /app-node