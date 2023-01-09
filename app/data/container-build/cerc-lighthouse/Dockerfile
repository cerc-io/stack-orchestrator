FROM sigp/lighthouse:v3.2.1-modern

RUN apt-get update; apt-get install bash netcat curl less jq -y;

WORKDIR /root/
ADD start-lighthouse.sh .

ENTRYPOINT [ "./start-lighthouse.sh" ]
