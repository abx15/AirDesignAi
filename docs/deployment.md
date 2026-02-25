# MotionMath AI: Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying MotionMath AI in production environments. The deployment is designed for enterprise-scale workloads with high availability, security, and scalability.

## Prerequisites

### Infrastructure Requirements
- **Kubernetes Cluster**: v1.25+ with at least 3 nodes
- **Node Specifications**: Minimum 4 CPU, 8GB RAM, 100GB SSD
- **Storage**: Fast SSD storage class (SSD or NVMe)
- **Network**: Load balancer support and static IP addresses
- **DNS**: Custom domain with SSL certificate management

### Tool Requirements
- **kubectl**: v1.25+
- **helm**: v3.8+
- **docker**: v20.10+
- **git**: v2.30+
- **openssl**: v1.1+

### Access Requirements
- **Cluster Admin**: Full Kubernetes cluster access
- **Container Registry**: Access to push/pull images
- **DNS Management**: Ability to manage DNS records
- **SSL Certificates**: Certificate management access

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/motionmath-ai.git
cd motionmath-ai
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Deploy Infrastructure
```bash
# Apply namespace and policies
kubectl apply -f infrastructure/kubernetes/namespace-enhanced.yaml

# Deploy secrets and configmaps
kubectl apply -f infrastructure/kubernetes/secrets-enhanced.yaml
kubectl apply -f infrastructure/kubernetes/configmap-enhanced.yaml
```

### 4. Deploy Services
```bash
# Deploy database
kubectl apply -f infrastructure/kubernetes/database-enhanced.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n motionmath-prod --timeout=300s

# Deploy Redis
kubectl apply -f infrastructure/kubernetes/redis.yaml

# Deploy application services
kubectl apply -f infrastructure/kubernetes/backend.yaml
kubectl apply -f infrastructure/kubernetes/frontend.yaml
kubectl apply -f infrastructure/kubernetes/celery.yaml
```

### 5. Configure Ingress
```bash
# Deploy ingress and load balancer
kubectl apply -f infrastructure/kubernetes/ingress-enhanced.yaml

# Configure DNS records
kubectl get ingress motionmath-ingress -n motionmath-prod
```

### 6. Setup Monitoring
```bash
# Run monitoring setup script
chmod +x scripts/monitoring-setup.sh
./scripts/monitoring-setup.sh
```

### 7. Verify Deployment
```bash
# Check pod status
kubectl get pods -n motionmath-prod

# Check services
kubectl get services -n motionmath-prod

# Test application
curl https://your-domain.com/health
```

## Detailed Deployment

### Environment Configuration

#### 1. Environment Variables
Create a `.env` file with the following configuration:

```bash
# Database Configuration
POSTGRES_USER=motionmath
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=motionmath
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PASSWORD=your_redis_password
REDIS_PORT=6379

# Application Configuration
NODE_ENV=production
LOG_LEVEL=INFO
DEBUG=false

# API Configuration
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret_key

# Frontend Configuration
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_ENVIRONMENT=production

# Monitoring Configuration
GRAFANA_PASSWORD=your_grafana_password
PROMETHEUS_PASSWORD=your_prometheus_password

# SSL Configuration
TLS_CERT_PATH=/path/to/your/certificate.crt
TLS_KEY_PATH=/path/to/your/private.key
```

#### 2. Secrets Management
Update the secrets in `infrastructure/kubernetes/secrets-enhanced.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: motionmath-secrets
  namespace: motionmath-prod
type: Opaque
data:
  # Base64 encoded values
  DATABASE_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-password>
  JWT_SECRET_KEY: <base64-encoded-secret>
  OPENAI_API_KEY: <base64-encoded-api-key>
```

### Database Deployment

#### 1. PostgreSQL Cluster
```bash
# Deploy PostgreSQL with high availability
kubectl apply -f infrastructure/kubernetes/database-enhanced.yaml

# Monitor deployment progress
kubectl get pods -l app=postgres -n motionmath-prod -w

# Verify database connectivity
kubectl exec -n motionmath-prod deployment/postgres -- psql -U motionmath -d motionmath -c "SELECT version();"
```

#### 2. Database Initialization
```bash
# Run database migrations
kubectl exec -n motionmath-prod deployment/backend -- alembic upgrade head

# Create initial data
kubectl exec -n motionmath-prod deployment/backend -- python scripts/init_data.py
```

### Application Deployment

#### 1. Backend Service
```bash
# Deploy backend API
kubectl apply -f infrastructure/kubernetes/backend.yaml

# Monitor rollout
kubectl rollout status deployment/backend-deployment -n motionmath-prod

# Scale to desired capacity
kubectl scale deployment backend-deployment --replicas=6 -n motionmath-prod
```

#### 2. Frontend Service
```bash
# Deploy frontend application
kubectl apply -f infrastructure/kubernetes/frontend.yaml

# Monitor rollout
kubectl rollout status deployment/frontend-deployment -n motionmath-prod

# Scale to desired capacity
kubectl scale deployment frontend-deployment --replicas=4 -n motionmath-prod
```

#### 3. Background Workers
```bash
# Deploy Celery workers
kubectl apply -f infrastructure/kubernetes/celery.yaml

# Monitor worker status
kubectl get pods -l app=celery-worker -n motionmath-prod
```

### Load Balancer Configuration

#### 1. Ingress Setup
```bash
# Deploy enhanced ingress with security features
kubectl apply -f infrastructure/kubernetes/ingress-enhanced.yaml

# Check ingress status
kubectl describe ingress motionmath-ingress -n motionmath-prod
```

#### 2. DNS Configuration
Update your DNS records to point to the load balancer:

```bash
# Get load balancer IP
kubectl get ingress motionmath-ingress -n motionmath-prod

# Update DNS records
# A record: your-domain.com -> LOAD_BALANCER_IP
# A record: api.your-domain.com -> LOAD_BALANCER_IP
```

#### 3. SSL Certificate
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create cluster issuer
kubectl apply -f infrastructure/ssl/cluster-issuer.yaml

# Request certificate
kubectl apply -f infrastructure/ssl/certificate.yaml
```

### Monitoring Setup

#### 1. Prometheus Stack
```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set grafana.adminPassword=admin123
```

#### 2. Application Metrics
```bash
# Deploy ServiceMonitors
kubectl apply -f infrastructure/monitoring/servicemonitors.yaml

# Configure Grafana dashboards
kubectl apply -f infrastructure/monitoring/dashboards.yaml
```

#### 3. Alerting
```bash
# Configure AlertManager
kubectl apply -f infrastructure/monitoring/alertmanager.yaml

# Set up notification channels
kubectl apply -f infrastructure/monitoring/receivers.yaml
```

## Security Hardening

### 1. Network Policies
```bash
# Apply network policies
kubectl apply -f infrastructure/kubernetes/namespace-enhanced.yaml

# Verify network isolation
kubectl get networkpolicy -n motionmath-prod
```

### 2. Pod Security
```bash
# Apply security contexts
kubectl apply -f infrastructure/kubernetes/security-policies.yaml

# Verify pod security
kubectl get pods -n motionmath-prod -o jsonpath='{.items[*].spec.securityContext}'
```

### 3. RBAC Configuration
```bash
# Apply RBAC policies
kubectl apply -f infrastructure/kubernetes/rbac.yaml

# Verify permissions
kubectl auth can-i create pods --as=system:serviceaccount:motionmath-prod:motionmath-backend-sa
```

## Scaling Configuration

### 1. Horizontal Pod Autoscaling
```bash
# Deploy HPA configurations
kubectl apply -f infrastructure/kubernetes/hpa-enhanced.yaml

# Monitor HPA status
kubectl get hpa -n motionmath-prod -w
```

### 2. Cluster Autoscaling
```bash
# Install cluster autoscaler
kubectl apply -f infrastructure/autoscaling/cluster-autoscaler.yaml

# Configure autoscaling parameters
kubectl edit configmap cluster-autoscaler-status -n kube-system
```

### 3. Resource Limits
```bash
# Apply resource quotas
kubectl apply -f infrastructure/kubernetes/namespace-enhanced.yaml

# Monitor resource usage
kubectl top pods -n motionmath-prod
```

## Backup and Recovery

### 1. Database Backups
```bash
# Create backup CronJob
kubectl apply -f infrastructure/backup/database-backup.yaml

# Verify backup schedule
kubectl get cronjob database-backup -n motionmath-prod
```

### 2. Disaster Recovery
```bash
# Create disaster recovery plan
kubectl apply -f infrastructure/backup/disaster-recovery.yaml

# Test recovery procedures
./scripts/test-disaster-recovery.sh
```

## Performance Optimization

### 1. Caching Strategy
```bash
# Deploy Redis cluster
kubectl apply -f infrastructure/kubernetes/redis-cluster.yaml

# Configure cache warming
kubectl apply -f infrastructure/cache/cache-warming.yaml
```

### 2. Database Optimization
```bash
# Apply database tuning
kubectl apply -f infrastructure/database/postgres-tuning.yaml

# Monitor performance
kubectl exec -n motionmath-prod deployment/postgres -- psql -U motionmath -d motionmath -c "SELECT * FROM pg_stat_activity;"
```

### 3. CDN Configuration
```bash
# Configure CloudFlare CDN
# Follow CloudFlare documentation to set up:
# - DNS records
# - SSL certificates
# - Caching rules
# - Security settings
```

## Troubleshooting

### Common Issues

#### 1. Pod Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n motionmath-prod

# Check logs
kubectl logs <pod-name> -n motionmath-prod

# Check events
kubectl get events -n motionmath-prod --sort-by='.lastTimestamp'
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
kubectl exec -n motionmath-prod deployment/backend -- python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://motionmath:password@postgres-service:5432/motionmath')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### 3. High Memory Usage
```bash
# Check memory usage
kubectl top pods -n motionmath-prod

# Analyze memory patterns
kubectl exec -n motionmath-prod deployment/backend -- python scripts/memory-analysis.py
```

#### 4. Slow Response Times
```bash
# Check resource utilization
kubectl top nodes
kubectl top pods -n motionmath-prod

# Analyze performance metrics
kubectl port-forward svc/prometheus-server 9090:80 -n monitoring
# Visit http://localhost:9090 to analyze metrics
```

### Debug Commands

#### 1. Service Connectivity
```bash
# Test service connectivity
kubectl exec -n motionmath-prod deployment/frontend -- curl -s http://backend-service/health

# Test database connectivity
kubectl exec -n motionmath-prod deployment/backend -- python -c "
import redis
r = redis.Redis(host='redis-service', port=6379, password='password')
print(r.ping())
"
```

#### 2. Configuration Verification
```bash
# Check environment variables
kubectl exec -n motionmath-prod deployment/backend -- env | grep DATABASE

# Check secrets
kubectl get secret motionmath-secrets -n motionmath-prod -o yaml
```

#### 3. Resource Analysis
```bash
# Check resource requests and limits
kubectl get pods -n motionmath-prod -o jsonpath='{.items[*].spec.containers[*].resources}'

# Check node capacity
kubectl describe nodes
```

## Maintenance

### 1. Rolling Updates
```bash
# Update application images
kubectl set image deployment/backend-deployment backend=ghcr.io/motionmath/motionmath-backend:v2.0.0 -n motionmath-prod

# Monitor rollout
kubectl rollout status deployment/backend-deployment -n motionmath-prod

# Rollback if needed
kubectl rollout undo deployment/backend-deployment -n motionmath-prod
```

### 2. Certificate Renewal
```bash
# Check certificate expiration
kubectl get certificate -n motionmath-prod

# Renew certificate
kubectl delete certificate motionmath-tls -n motionmath-prod
kubectl apply -f infrastructure/ssl/certificate.yaml
```

### 3. Log Management
```bash
# Configure log rotation
kubectl apply -f infrastructure/logging/log-rotation.yaml

# Check log storage
kubectl get persistentvolumeclaim -n motionmath-prod
```

## Monitoring and Alerting

### 1. Key Metrics
- **Response Time**: < 200ms (95th percentile)
- **Error Rate**: < 0.1%
- **CPU Usage**: < 70%
- **Memory Usage**: < 80%
- **Database Connections**: < 80% of max

### 2. Alert Thresholds
- **Critical**: Service downtime, high error rate
- **Warning**: High resource usage, slow queries
- **Info**: Deployments, configuration changes

### 3. Dashboard Access
- **Grafana**: https://grafana.your-domain.com
- **Prometheus**: https://prometheus.your-domain.com
- **Kibana**: https://logs.your-domain.com

## Support

### Documentation
- [Architecture Documentation](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

### Community
- GitHub Issues: https://github.com/your-org/motionmath-ai/issues
- Discussions: https://github.com/your-org/motionmath-ai/discussions
- Wiki: https://github.com/your-org/motionmath-ai/wiki

### Professional Support
- Email: support@motionmath.ai
- Slack: #motionmath-support
- Phone: +1-555-MOTIONMATH

## Conclusion

This deployment guide provides a comprehensive approach to deploying MotionMath AI in production environments. The infrastructure is designed for enterprise-scale workloads with high availability, security, and scalability.

For additional support or questions, please refer to the documentation or contact the support team.
