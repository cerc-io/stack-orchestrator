# Helm Chart Generation

Generate Kubernetes Helm charts from stack compose files using Kompose.

## Prerequisites

Install Kompose:

```bash
# Linux
curl -L https://github.com/kubernetes/kompose/releases/download/v1.34.0/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/

# macOS
brew install kompose

# Verify
kompose version
```

## Usage

### 1. Create spec file

```bash
laconic-so --stack <stack-name> deploy --deploy-to k8s init \
  --kube-config ~/.kube/config \
  --output spec.yml
```

### 2. Generate Helm chart

```bash
laconic-so --stack <stack-name> deploy create \
  --spec-file spec.yml \
  --deployment-dir my-deployment \
  --helm-chart
```

### 3. Deploy to Kubernetes

```bash
helm install my-release my-deployment/chart
kubectl get pods -n zenith
```

## Output Structure

```bash
my-deployment/
├── spec.yml              # Reference
├── stack.yml             # Reference
└── chart/                # Helm chart
  ├── Chart.yaml
  ├── README.md
  └── templates/
    └── *.yaml
```

## Example

```bash
# Generate chart for stage1-zenithd
laconic-so --stack stage1-zenithd deploy --deploy-to k8s init \
  --kube-config ~/.kube/config \
  --output stage1-spec.yml

laconic-so --stack stage1-zenithd deploy create \
  --spec-file stage1-spec.yml \
  --deployment-dir stage1-deployment \
  --helm-chart

# Deploy
helm install stage1-zenithd stage1-deployment/chart
```

## Production Deployment (TODO)

### Local Development

```bash
# Access services using port-forward
kubectl port-forward service/zenithd 26657:26657
kubectl port-forward service/nginx-api-proxy 1317:80
kubectl port-forward service/cosmos-explorer 4173:4173
```

### Production Access Options

- Option 1: Ingress + cert-manager (Recommended)
  - Install ingress-nginx + cert-manager
  - Point DNS to cluster LoadBalancer IP
  - Auto-provisions Let's Encrypt TLS certs
  - Access: `https://api.zenith.example.com`
- Option 2: Cloud LoadBalancer
  - Use cloud provider's LoadBalancer service type
  - Point DNS to assigned external IP
  - Manual TLS cert management
- Option 3: Bare Metal (MetalLB + Ingress)
  - MetalLB provides LoadBalancer IPs from local network
  - Same Ingress setup as cloud
- Option 4: NodePort + External Proxy
  - Expose services on 30000-32767 range
  - External nginx/Caddy proxies 80/443 → NodePort
  - Manual cert management

### Changes Needed

- Add Ingress template to charts
- Add TLS configuration to values.yaml
- Document cert-manager setup
- Add production deployment guide
