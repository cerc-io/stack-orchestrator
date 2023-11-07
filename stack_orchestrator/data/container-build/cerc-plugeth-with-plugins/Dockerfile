# Using the same golang image as used to build plugeth: https://git.vdb.to/cerc-io/plugeth/src/branch/statediff/Dockerfile
FROM golang:1.20-alpine3.18 as delve

# Add delve so that we can do remote debugging.
RUN go install github.com/go-delve/delve/cmd/dlv@latest

FROM cerc/plugeth-statediff:local as statediff
FROM cerc/plugeth:local as plugeth

FROM alpine:3.18

# Install tools often used in scripting, like bash, wget, and jq.
RUN apk add --no-cache ca-certificates bash wget curl python3 bind-tools postgresql-client jq

COPY --from=delve /go/bin/dlv /usr/local/bin/
COPY --from=plugeth /usr/local/bin/geth /usr/local/bin/

# Place all plugeth plugins in /usr/local/lib/plugeth
COPY --from=statediff  /usr/local/lib/statediff.so /usr/local/lib/plugeth/

EXPOSE 8545 8546 8551 6060 30303 30303/udp 40000
ENTRYPOINT ["geth"]
