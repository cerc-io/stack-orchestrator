FROM cerc/lighthouse-base:local

RUN apt-get update; apt-get install bash netcat curl less jq -y;

WORKDIR /root/
ADD start-lighthouse.sh .

ENTRYPOINT [ "./start-lighthouse.sh" ]
