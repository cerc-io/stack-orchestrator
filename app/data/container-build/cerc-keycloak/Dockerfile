FROM quay.io/keycloak/keycloak:20.0
WORKDIR /opt/keycloak/providers
RUN curl -L https://github.com/aerogear/keycloak-metrics-spi/releases/download/2.5.3/keycloak-metrics-spi-2.5.3.jar --output keycloak-metrics-spi.jar
RUN curl -L https://github.com/cerc-io/keycloak-api-key-demo/releases/download/v0.1/api-key-module-0.1.jar --output api-key-module.jar
