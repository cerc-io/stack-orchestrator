FROM sigp/lighthouse:v5.1.2

RUN apt-get update && apt-get -y upgrade \
    && apt-get -y install bash netcat curl less jq wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /root
ADD start-lighthouse.sh .

ENTRYPOINT [ "./start-lighthouse.sh" ]
