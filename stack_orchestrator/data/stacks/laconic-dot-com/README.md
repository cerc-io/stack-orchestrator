# laconic-dot-com

```
laconic-so --stack laconic-dot-com setup-repositories
laconic-so --stack laconic-dot-com build-containers
laconic-so --stack laconic-dot-com deploy init --output laconic-website-spec.yml --map-ports-to-host localhost-same
laconic-so --stack laconic-dot-com deploy create --spec-file laconic-website-spec.yml --deployment-dir lx-website
laconic-so deployment --dir lx-website start
```
