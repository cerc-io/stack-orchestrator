FROM golang:1.21-bullseye AS builder

# Copy files into image
WORKDIR /app
COPY . .

# Build the binary
RUN go build -v -o nitro .

# Reduce image size
FROM debian:bullseye-slim
RUN apt-get update
RUN apt-get install -y ca-certificates jq netcat
RUN rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app/nitro .
