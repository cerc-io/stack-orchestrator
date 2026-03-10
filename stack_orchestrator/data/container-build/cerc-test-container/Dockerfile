FROM alpine:latest

RUN apk add --no-cache nginx

EXPOSE 80

COPY run.sh /app/run.sh

ENTRYPOINT ["/app/run.sh"]
