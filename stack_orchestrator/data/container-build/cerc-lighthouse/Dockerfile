ARG TAG_SUFFIX="-modern"
FROM sigp/lighthouse:v4.3.0${TAG_SUFFIX}

RUN apt-get update; apt-get install bash netcat curl less jq wget -y;

WORKDIR /root/
ADD start-lighthouse.sh .

ENTRYPOINT [ "./start-lighthouse.sh" ]
