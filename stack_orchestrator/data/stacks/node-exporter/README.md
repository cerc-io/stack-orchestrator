# node-exporter

## Start the stack

```bash
laconic-so --stack node-exporter deploy up
```

* The host node's metrics can be accessed at `http://localhost:9100/metrics`

## Clean up

Stop the node-exporter running in background:

```bash
laconic-so --stack node-exporter deploy down
```
