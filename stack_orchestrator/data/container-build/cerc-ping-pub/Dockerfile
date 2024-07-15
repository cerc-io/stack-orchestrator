FROM cerc/ping-pub-base:local

COPY ./scripts/update-explorer-config.sh /scripts
COPY ./scripts/start-serving-explorer.sh /scripts
COPY ./config/laconic-chaindata-template.json /config/chains/laconic-chaindata-template.json

EXPOSE 5173

WORKDIR /app
CMD ["/scripts/start-serving-explorer.sh"]
