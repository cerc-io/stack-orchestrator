FROM maven:3-eclipse-temurin-11-alpine AS builder
RUN apk add --update --no-cache git
WORKDIR /build
RUN git clone https://github.com/cerc-io/keycloak-api-key-demo.git && \
      cd keycloak-api-key-demo && \
      git checkout '043309204aba4c3cb2f6a006c58a9a430b733b29' && \
      mvn -f api-key-module package

FROM quay.io/keycloak/keycloak:20.0
COPY --from=builder /build/keycloak-api-key-demo//api-key-module/target/deploy/*  /opt/keycloak/providers/
WORKDIR /opt/keycloak/providers
RUN curl -L https://github.com/aerogear/keycloak-metrics-spi/releases/download/2.5.3/keycloak-metrics-spi-2.5.3.jar --output keycloak-metrics-spi.jar
