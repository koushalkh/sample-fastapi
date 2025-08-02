# Deployment Guide

This document provides comprehensive deployment instructions for the ADR FastAPI microservice across different environments.

## Overview

The ADR microservice supports multiple deployment scenarios:

- **Local Development**: Direct Python execution or containerized
- **Container Deployment**: Docker-based deployment
- **Kubernetes Deployment**: Scalable container orchestration (planned)
- **Cloud Deployment**: Cloud-native deployment options (planned)

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Memory**: Minimum 512MB, Recommended 1GB+
- **CPU**: Minimum 1 core, Recommended 2+ cores
- **Storage**: 1GB for application and dependencies

### Dependencies

- **uv** (recommended) or **pip** for package management
- **Docker** (for containerized deployment)
- **Kubernetes** (for orchestrated deployment)

## Local Development Deployment

### Quick Start

The fastest way to run the service locally:

```bash
# Navigate to project directory
cd /path/to/sample

# Run with the provided script
./scripts/start.sh
```

### Manual Setup

If you prefer manual setup:

1. **Environment Setup**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install dependencies (if requirements.txt exists)
   pip install -r requirements.txt
   
   # Or install from pyproject.toml
   pip install -e .
   ```

2. **Environment Variables**
   ```bash
   export PYTHONPATH="./app"
   export POD_NAMESPACE="development"  # For dev environment detection
   export API_MODE="ALL"               # Optional, defaults to ALL
   ```

3. **Start the Application**
   ```bash
   # Direct Python execution
   python app/main.py --api-mode ALL

   # Or with uvicorn
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Using UV Package Manager

For faster dependency management:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Run the application
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Development Configuration

Create a `.env` file for local development:

```bash
# .env
POD_NAMESPACE=development
PYTHONPATH=./app
API_MODE=ALL
```

### Verification

After starting the service, verify it's running:

```bash
# Health check
curl http://localhost:8000/healthz

# API documentation
open http://localhost:8000/docs
```

## Container Deployment

### Building the Container

The service includes a multi-stage Dockerfile optimized for production:

```bash
# Build the container image
docker build -f docker/Dockerfile -t adr-service:latest .

# Build with specific version tag
docker build -f docker/Dockerfile -t adr-service:1.0.0 .
```

### Running with Docker

#### Basic Container Run

```bash
# Run with default settings
docker run -p 8000:8000 adr-service:latest

# Run with environment variables
docker run -p 8000:8000 \
  -e API_MODE=ALL \
  -e POD_NAMESPACE=production \
  adr-service:latest

# Run in detached mode
docker run -d -p 8000:8000 \
  --name adr-service \
  -e API_MODE=ALL \
  adr-service:latest
```

#### Container with Custom Configuration

```bash
# Run with custom port
docker run -p 9000:8000 \
  -e PORT=8000 \
  adr-service:latest

# Run with mounted configuration
docker run -p 8000:8000 \
  -v $(pwd)/config:/opt/adr/config \
  adr-service:latest
```

### Docker Compose

Create a `docker-compose.yml` for easy management:

```yaml
version: '3.8'

services:
  adr-service:
    image: adr-service:latest
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - API_MODE=ALL
      - POD_NAMESPACE=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Future: Add database, redis, etc.
  # postgres:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_DB: adr
  #     POSTGRES_USER: adr
  #     POSTGRES_PASSWORD: password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
```

Run with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f adr-service

# Stop services
docker-compose down
```

## Kubernetes Deployment

*Note: Kubernetes manifests are planned for future implementation.*

### Basic Deployment Manifest

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adr-service
  labels:
    app: adr-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: adr-service
  template:
    metadata:
      labels:
        app: adr-service
    spec:
      containers:
      - name: adr-service
        image: adr-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_MODE
          value: "ALL"
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Service and Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: adr-service
spec:
  selector:
    app: adr-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: adr-service
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: adr.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: adr-service
            port:
              number: 80
```

### Deployment Commands

```bash
# Apply manifests
kubectl apply -f deploy/

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -l app=adr-service -f

# Scale deployment
kubectl scale deployment adr-service --replicas=5
```

## Environment-Specific Configurations

### Development Environment

```bash
# Environment variables
export POD_NAMESPACE=development
export API_MODE=ALL
export LOG_LEVEL=DEBUG

# Container run
docker run -p 8000:8000 \
  -e POD_NAMESPACE=development \
  -e API_MODE=ALL \
  adr-service:latest
```

### Staging Environment

```bash
# Environment variables
export POD_NAMESPACE=staging
export API_MODE=ALL
export LOG_LEVEL=INFO

# Container run with resource limits
docker run -p 8000:8000 \
  --memory="512m" \
  --cpus="1.0" \
  -e POD_NAMESPACE=staging \
  -e API_MODE=ALL \
  adr-service:latest
```

### Production Environment

```bash
# Environment variables
export POD_NAMESPACE=production
export API_MODE=ALL
export LOG_LEVEL=INFO

# Container run with production settings
docker run -p 8000:8000 \
  --memory="1g" \
  --cpus="2.0" \
  --restart=unless-stopped \
  -e POD_NAMESPACE=production \
  -e API_MODE=ALL \
  adr-service:latest
```

## Load Balancing and High Availability

### Multiple Container Instances

Run multiple instances with a load balancer:

```bash
# Run multiple containers
for i in {1..3}; do
  docker run -d --name adr-service-$i \
    -p $((8000 + $i)):8000 \
    -e POD_NAMESPACE=production \
    adr-service:latest
done

# Use nginx or other load balancer to distribute traffic
```

### Health Check Configuration

Configure health checks for load balancers:

```bash
# Health check endpoint
curl -f http://localhost:8000/healthz || exit 1

# Readiness check endpoint
curl -f http://localhost:8000/readyz || exit 1
```

## Monitoring and Logging

### Application Logs

```bash
# View container logs
docker logs adr-service -f

# View Kubernetes logs
kubectl logs -l app=adr-service -f

# Log aggregation (planned)
# - Fluentd/Fluent Bit
# - ELK Stack
# - Grafana Loki
```

### Health Monitoring

```bash
# Health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz)
if [ $response -eq 200 ]; then
  echo "Service is healthy"
else
  echo "Service is unhealthy: HTTP $response"
  exit 1
fi
```

### Performance Monitoring

```bash
# Container resource usage
docker stats adr-service

# Kubernetes resource usage
kubectl top pods -l app=adr-service
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill process or use different port
   docker run -p 8001:8000 adr-service:latest
   ```

2. **Container Build Failures**
   ```bash
   # Build with verbose output
   docker build --no-cache -f docker/Dockerfile -t adr-service:latest .
   
   # Check build context
   docker build --progress=plain -f docker/Dockerfile .
   ```

3. **Health Check Failures**
   ```bash
   # Check service logs
   docker logs adr-service
   
   # Test health endpoint manually
   curl -v http://localhost:8000/healthz
   ```

4. **Environment Detection Issues**
   ```bash
   # Verify environment variables
   docker run --rm adr-service:latest env | grep POD_NAMESPACE
   
   # Override environment detection
   docker run -e POD_NAMESPACE=production adr-service:latest
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Run with debug environment
docker run -p 8000:8000 \
  -e POD_NAMESPACE=development \
  -e LOG_LEVEL=DEBUG \
  adr-service:latest
```

### Performance Tuning

```bash
# Run with multiple workers
docker run -p 8000:8000 \
  -e WORKERS=4 \
  adr-service:latest

# Adjust memory limits
docker run -p 8000:8000 \
  --memory="2g" \
  adr-service:latest
```

## Backup and Recovery

### Container Data Backup

```bash
# Backup container configuration
docker inspect adr-service > adr-service-config.json

# Export container image
docker save adr-service:latest | gzip > adr-service-backup.tar.gz
```

### Database Backup (Future)

```bash
# Planned: Database backup procedures
# pg_dump, automated backups, point-in-time recovery
```

## Security Considerations

### Container Security

```bash
# Run as non-root user (already configured in Dockerfile)
# Scan image for vulnerabilities
docker scan adr-service:latest

# Use specific version tags
docker build -t adr-service:1.0.0 .
```

### Network Security

```bash
# Use internal networks
docker network create adr-network
docker run --network adr-network adr-service:latest

# Implement TLS termination at load balancer
```

### Secrets Management

```bash
# Use environment files for secrets
docker run --env-file .env.production adr-service:latest

# Use Kubernetes secrets (planned)
kubectl create secret generic adr-secrets --from-literal=db-password=secret
```

## Maintenance

### Rolling Updates

```bash
# Kubernetes rolling update
kubectl set image deployment/adr-service adr-service=adr-service:1.1.0

# Docker Compose update
docker-compose pull
docker-compose up -d
```

### Scaling

```bash
# Horizontal scaling
kubectl scale deployment adr-service --replicas=10

# Vertical scaling (resource adjustment)
kubectl patch deployment adr-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"adr-service","resources":{"limits":{"memory":"1Gi","cpu":"1000m"}}}]}}}}'
```
