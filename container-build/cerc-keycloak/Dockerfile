FROM maven:3-eclipse-temurin-11-alpine AS builder
RUN apk add --update --no-cache git
WORKDIR /build
RUN git clone https://github.com/cerc-io/keycloak-api-key-demo.git
RUN cd keycloak-api-key-demo && \
      git checkout 81d0a443c363cb55df2c90e3b13fc5a4710197ba && \
      mvn -f api-key-module package

FROM quay.io/keycloak/keycloak:19.0.2
COPY --from=builder /build/keycloak-api-key-demo//api-key-module/target/deploy/*  /opt/keycloak/providers/
