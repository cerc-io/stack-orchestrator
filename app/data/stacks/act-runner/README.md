# act-runner stack

## Example

```
$ laconic-so --stack act-runner deploy init --output act-runner.yml

$ laconic-so --stack act-runner deploy create --spec-file act-runner.yml --deployment-dir ~/opt/deployments/act-runner-1
$ echo "CERC_GITEA_RUNNER_REGISTRATION_TOKEN=FOO" >> ~/opt/deployments/act-runner-1/config.env
$ laconic-so deployment --dir ~/opt/deployments/act-runner-1 up

$ laconic-so --stack act-runner deploy create --spec-file act-runner.yml --deployment-dir ~/opt/deployments/act-runner-2
$ echo "CERC_GITEA_RUNNER_REGISTRATION_TOKEN=BAR" >> ~/opt/deployments/act-runner-2/config.env
$ laconic-so deployment --dir ~/opt/deployments/act-runner-2 up
```
