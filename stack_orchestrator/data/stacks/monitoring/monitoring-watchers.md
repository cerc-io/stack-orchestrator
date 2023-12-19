# Monitoring Watchers

Instructions to setup and run monitoring stack with pre-configured watcher dashboards

## Create a deployment

First, create a spec file for the deployment, which will map the stack's ports and volumes to the host:

```bash
laconic-so --stack monitoring deploy init --output monitoring-watchers-spec.yml
```

### Ports

Edit `network` in spec file to map container ports to same ports in host:

```
...
network:
  ports:
    prometheus:
      - '9090:9090'
    grafana:
      - '3000:3000'
...
```

---

Once you've made any needed changes to the spec file, create a deployment from it:

```bash
laconic-so --stack monitoring deploy create --spec-file monitoring-watchers-spec.yml --deployment-dir monitoring-watchers-deployment
```

## Configure

### Prometheus Config

Add the following scrape configs to prometheus config file (`monitoring-watchers-deployment/config/monitoring/prometheus/prometheus.yml`) in the deployment folder:

  ```yml
  ...
  - job_name: 'blackbox'
    ...
    static_configs:
      - targets:
        - <AZIMUTH_GATEWAY_GQL_ENDPOINT>
  ...
  - job_name: azimuth
    scrape_interval: 10s
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets: ['AZIMUTH_WATCHER_HOST:AZIMUTH_WATCHER_PORT']
        labels:
          instance: 'azimuth'
      - targets: ['CENSURES_WATCHER_HOST:CENSURES_WATCHER_PORT']
        labels:
          instance: 'censures'
      - targets: ['CLAIMS_WATCHER_HOST:CLAIMS_WATCHER_PORT']
        labels:
          instance: 'claims'
      - targets: ['CONDITIONAL_STAR_RELEASE_WATCHER_HOST:CONDITIONAL_STAR_RELEASE_WATCHER_PORT']
        labels:
          instance: 'conditional_star_release'
      - targets: ['DELEGATED_SENDING_WATCHER_HOST:DELEGATED_SENDING_WATCHER_PORT']
        labels:
          instance: 'delegated_sending_watcher'
      - targets: ['ECLIPTIC_WATCHER_HOST:ECLIPTIC_WATCHER_PORT']
        labels:
          instance: 'ecliptic'
      - targets: ['LINEAR_STAR_WATCHER_HOST:LINEAR_STAR_WATCHER_PORT']
        labels:
          instance: 'linear_star_release'
      - targets: ['POLLS_WATCHER_HOST:POLLS_WATCHER_PORT']
        labels:
          instance: 'polls'

  - job_name: sushi
    scrape_interval: 20s
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets: ['SUSHISWAP_WATCHER_HOST:SUSHISWAP_WATCHER_PORT']
        labels:
          instance: 'sushiswap'
      - targets: ['MERKLE_SUSHISWAP_WATCHER_HOST:MERKLE_SUSHISWAP_WATCHER_PORT']
        labels:
          instance: 'merkl_sushiswap'
  ```

### Grafana Config

In the deployment folder, copy over the pre-configured watcher dashboard JSON files to grafana dashboards config directory:

```bash
cp -r monitoring-watchers-deployment/config/monitoring/grafana/watcher-dashboards/* monitoring-watchers-deployment/config/monitoring/grafana/dashboards/
```

## Start the stack

Start the deployment:

```bash
laconic-so deployment --dir monitoring-watchers-deployment start
```

* List and check the health status of all the containers using `docker ps` and wait for them to be `healthy`

* Grafana should now be visible at http://localhost:3000 with configured dashboards

## Clean up

To stop monitoring services running in the background, while preserving data:

```bash
# Only stop the docker containers
laconic-so deployment --dir monitoring-watchers-deployment stop

# Run 'start' to restart the deployment
```

To stop monitoring services and also delete data:

```bash
# Stop the docker containers
laconic-so deployment --dir monitoring-watchers-deployment stop --delete-volumes

# Remove deployment directory (deployment will have to be recreated for a re-run)
rm -rf monitoring-watchers-deployment
```
