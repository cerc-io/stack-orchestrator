FROM ubuntu:latest

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && export DEBCONF_NOWARNINGS="yes" && \
    apt-get install -y software-properties-common && \
    apt-get install -y nginx && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 80

COPY run.sh /app/run.sh

ENTRYPOINT ["/app/run.sh"]
