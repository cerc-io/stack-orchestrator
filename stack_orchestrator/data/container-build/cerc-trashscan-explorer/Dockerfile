FROM cerc/trashscan-explorer-base:local

COPY ./scripts/start-explorer.sh /scripts/

WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD nc -z localhost 5000 || exit 1

CMD ["/scripts/start-explorer.sh"]
