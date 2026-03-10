# act-runner stack

## Example

```
$ laconic-so --stack act-runner deploy init --output act-runner-1.yml --config CERC_GITEA_RUNNER_REGISTRATION_TOKEN=FOO
$ laconic-so --stack act-runner deploy create --spec-file act-runner-1.yml --deployment-dir ~/opt/deployments/act-runner-1
$ laconic-so deployment --dir ~/opt/deployments/act-runner-1 up

$ laconic-so --stack act-runner deploy init --output act-runner-2.yml --config CERC_GITEA_RUNNER_REGISTRATION_TOKEN=BAR
$ laconic-so --stack act-runner deploy create --spec-file act-runner-2.yml --deployment-dir ~/opt/deployments/act-runner-2
$ laconic-so deployment --dir ~/opt/deployments/act-runner-2 up
```
