#!/bin/bash

echo Using CERC_GRAFANA_ALERTS_SUBGRAPH_IDS ${CERC_GRAFANA_ALERTS_SUBGRAPH_IDS}

# Replace subgraph ids in subgraph alerting config
# Note: Requires the grafana container to be run with user root
if [ -n "$CERC_GRAFANA_ALERTS_SUBGRAPH_IDS" ]; then
  sed -i "s/REPLACE_WITH_SUBGRAPH_IDS/$CERC_GRAFANA_ALERTS_SUBGRAPH_IDS/g" /etc/grafana/provisioning/alerting/subgraph-alert-rules.yml
fi
