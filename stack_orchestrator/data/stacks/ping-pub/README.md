# ping-pub
Experimental block explorer for laconic

```
laconic-so --stack ping-pub setup-repositories
laconic-so --stack ping-pub build-containers
laconic-so --stack ping-pub deploy init --output ping-pub-spec.yml --map-ports-to-host localhost-same
laconic-so --stack ping-pub deploy create --spec-file ping-pub-spec.yml --deployment-dir pp-deployment
laconic-so deployment --dir pp-deployment start
```
