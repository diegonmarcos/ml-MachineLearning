# Deployment & Infrastructure Guide

## Overview

This guide provides comprehensive instructions for deploying the n8n Model Orchestration Platform, from local development to production environments.

## Deployment Options

1. **Local Development**: Docker Compose
2. **Production**: Kubernetes (recommended)
3. **Cloud Managed**: AWS/GCP/Azure with managed services
4. **Hybrid**: Self-hosted with managed databases

## Prerequisites

### Required Software
- Docker 24.0+
- Docker Compose 2.20+
- Kubernetes 1.28+ (for production)
- kubectl CLI
- Helm 3.12+
- Terraform 1.5+ (optional, for infrastructure as code)

### Required Accounts
- VPS Provider accounts (RunPod, Vast.ai, Lambda Labs, etc.)
- Cloud provider account (AWS/GCP/Azure)
- GitHub account (for version control)
- Docker Hub account (for container registry)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ml-orchestration-platform.git
cd ml-orchestration-platform
```

### 2. Environment Configuration

Create `.env` file:

```bash
# API Configuration
API_URL=http://localhost:8000
API_SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-change-in-production
JWT_EXPIRY=3600

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ml_platform
POSTGRES_USER=mluser
POSTGRES_PASSWORD=change-me-in-production

# TimescaleDB
TIMESCALEDB_HOST=timescaledb
TIMESCALEDB_PORT=5432
TIMESCALEDB_DB=metrics
TIMESCALEDB_USER=tsuser
TIMESCALEDB_PASSWORD=change-me-in-production

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=change-me-in-production

# n8n
N8N_HOST=n8n
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change-me-in-production
N8N_ENCRYPTION_KEY=your-encryption-key

# MinIO (Object Storage)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change-me-in-production
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=ml-platform

# Provider API Keys
RUNPOD_API_KEY=your-runpod-api-key
VAST_API_KEY=your-vast-api-key
LAMBDA_API_KEY=your-lambda-api-key
MODAL_TOKEN=your-modal-token

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=change-me-in-production

# Frontend
REACT_APP_API_URL=http://localhost:8000/v1
REACT_APP_WS_URL=ws://localhost:8000

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # TimescaleDB for metrics
  timescaledb:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: ${TIMESCALEDB_DB}
      POSTGRES_USER: ${TIMESCALEDB_USER}
      POSTGRES_PASSWORD: ${TIMESCALEDB_PASSWORD}
    volumes:
      - timescale_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # MinIO Object Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # n8n Workflow Automation
  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${POSTGRES_DB}
      - DB_POSTGRESDB_USER=${POSTGRES_USER}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_METRICS=true
      - N8N_METRICS_INCLUDE_DEFAULT_METRICS=true
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/home/node/.n8n/workflows
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # API Backend
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - PROVIDER_RUNPOD_KEY=${RUNPOD_API_KEY}
      - PROVIDER_VAST_KEY=${VAST_API_KEY}
      - PROVIDER_LAMBDA_KEY=${LAMBDA_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
      - minio
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - REACT_APP_API_URL=${REACT_APP_API_URL}
      - REACT_APP_WS_URL=${REACT_APP_WS_URL}
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - api

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Grafana Visualization
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  timescale_data:
  redis_data:
  minio_data:
  n8n_data:
  prometheus_data:
  grafana_data:
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### 5. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Seed data (optional)
docker-compose exec api python scripts/seed_data.py
```

### 6. Access Services

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **n8n**: http://localhost:5678
- **MinIO Console**: http://localhost:9001
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## Production Deployment (Kubernetes)

### 1. Cluster Setup

#### Using Managed Kubernetes

**AWS EKS:**
```bash
eksctl create cluster \
  --name ml-platform \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

**GCP GKE:**
```bash
gcloud container clusters create ml-platform \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10
```

**Azure AKS:**
```bash
az aks create \
  --resource-group ml-platform-rg \
  --name ml-platform \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10
```

### 2. Install Dependencies

```bash
# Install cert-manager (for SSL)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/cloud/deploy.yaml

# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Install PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --set auth.database=ml_platform \
  --set auth.username=mluser \
  --set persistence.size=100Gi
```

### 3. Deploy Application

Create Kubernetes manifests:

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-platform
```

**configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: ml-platform
data:
  API_URL: "https://api.mlplatform.com"
  POSTGRES_HOST: "postgres-postgresql"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "ml_platform"
  REDIS_HOST: "redis-master"
  REDIS_PORT: "6379"
```

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: ml-platform
type: Opaque
stringData:
  JWT_SECRET: "your-jwt-secret"
  POSTGRES_PASSWORD: "your-db-password"
  REDIS_PASSWORD: "your-redis-password"
  RUNPOD_API_KEY: "your-runpod-key"
  VAST_API_KEY: "your-vast-key"
  LAMBDA_API_KEY: "your-lambda-key"
```

**api-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: ml-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/ml-platform-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)"
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: ml-platform
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

**frontend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: ml-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/ml-platform-frontend:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: ml-platform
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
```

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ml-platform-ingress
  namespace: ml-platform
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - mlplatform.com
    - api.mlplatform.com
    secretName: ml-platform-tls
  rules:
  - host: mlplatform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
  - host: api.mlplatform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
```

**Deploy:**
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### 4. Auto-Scaling Configuration

**HorizontalPodAutoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: ml-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 5. Monitoring Setup

**ServiceMonitor for Prometheus:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-metrics
  namespace: ml-platform
spec:
  selector:
    matchLabels:
      app: api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

## CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/deploy.yml:**
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov=./ --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push API
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: your-registry/ml-platform-api:${{ github.sha }},your-registry/ml-platform-api:latest

      - name: Build and push Frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: your-registry/ml-platform-frontend:${{ github.sha }},your-registry/ml-platform-frontend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api api=your-registry/ml-platform-api:${{ github.sha }} -n ml-platform
          kubectl set image deployment/frontend frontend=your-registry/ml-platform-frontend:${{ github.sha }} -n ml-platform
          kubectl rollout status deployment/api -n ml-platform
          kubectl rollout status deployment/frontend -n ml-platform
```

## Database Migrations

### Using Alembic

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Backup & Restore

### Database Backup

```bash
# Backup PostgreSQL
kubectl exec -n ml-platform postgres-0 -- pg_dump -U mluser ml_platform > backup.sql

# Restore
kubectl exec -n ml-platform postgres-0 -- psql -U mluser ml_platform < backup.sql
```

### Object Storage Backup

```bash
# Backup MinIO data
mc mirror minio/ml-platform s3/backup/ml-platform
```

## Security Hardening

### 1. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: ml-platform
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### 2. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-platform
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 3. Secrets Management with Vault

```bash
# Install Vault
helm install vault hashicorp/vault

# Configure Vault
vault secrets enable -path=ml-platform kv-v2
vault kv put ml-platform/api \
  jwt_secret="your-secret" \
  db_password="your-password"
```

## Monitoring & Alerting

### Prometheus Alerts

**alerts.yaml:**
```yaml
groups:
- name: ml-platform
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"

  - alert: PodDown
    expr: up{job="ml-platform-api"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "API pod is down"

  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## Troubleshooting

### Common Issues

**1. Database Connection Issues:**
```bash
# Check database status
kubectl get pods -n ml-platform | grep postgres

# View logs
kubectl logs -n ml-platform postgres-0

# Test connection
kubectl exec -it -n ml-platform api-xxx -- psql -h postgres -U mluser -d ml_platform
```

**2. API Not Responding:**
```bash
# Check pod status
kubectl get pods -n ml-platform

# View logs
kubectl logs -n ml-platform api-xxx

# Describe pod
kubectl describe pod -n ml-platform api-xxx
```

**3. Out of Memory:**
```bash
# Check resource usage
kubectl top pods -n ml-platform

# Increase limits
kubectl set resources deployment api --limits=memory=4Gi -n ml-platform
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_jobs_user_id ON training_jobs(user_id);
CREATE INDEX idx_jobs_status ON training_jobs(status);
CREATE INDEX idx_cost_tracking_job_id ON cost_tracking(job_id);
CREATE INDEX idx_cost_tracking_timestamp ON cost_tracking(timestamp DESC);

-- Vacuum and analyze
VACUUM ANALYZE;
```

### 2. Redis Caching

```python
# Cache frequently accessed data
@cache(expire=300)
def get_active_jobs():
    return db.query(TrainingJob).filter(status='running').all()
```

### 3. CDN for Frontend

Use CloudFlare or AWS CloudFront for static assets.

## Cost Optimization

### 1. Use Spot Instances

```yaml
# AWS EKS with spot instances
nodeSelector:
  eks.amazonaws.com/capacityType: SPOT
```

### 2. Auto-Scaling

- Scale down non-production environments during off-hours
- Use cluster autoscaler
- Implement pod disruption budgets

### 3. Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ml-platform-quota
  namespace: ml-platform
spec:
  hard:
    requests.cpu: "50"
    requests.memory: 100Gi
    limits.cpu: "100"
    limits.memory: 200Gi
```

## Summary

This deployment guide provides:

- **Local Development**: Quick setup with Docker Compose
- **Production Deployment**: Kubernetes with high availability
- **CI/CD**: Automated testing and deployment
- **Monitoring**: Comprehensive observability
- **Security**: Best practices for production
- **Scalability**: Auto-scaling and load balancing
- **Disaster Recovery**: Backup and restore procedures

Follow these guidelines to ensure a reliable, secure, and scalable deployment of the ML Orchestration Platform.
