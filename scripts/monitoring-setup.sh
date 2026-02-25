#!/bin/bash
# Performance monitoring and alerting script for MotionMath AI
# This script sets up comprehensive monitoring for production workloads

set -euo pipefail

# Configuration
NAMESPACE="motionmath-prod"
MONITORING_NAMESPACE="monitoring"
LOG_FILE="/var/log/motionmath-monitoring.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Install Prometheus Operator
install_prometheus_operator() {
    log "Installing Prometheus Operator..."
    
    # Create monitoring namespace
    kubectl create namespace "$MONITORING_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Install kube-prometheus-stack
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace "$MONITORING_NAMESPACE" \
        --set prometheus.prometheusSpec.retention=30d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
        --set grafana.adminPassword=admin123 \
        --set grafana.persistence.enabled=true \
        --set grafana.persistence.size=10Gi \
        --set alertmanager.enabled=true \
        --set alertmanager.persistence.enabled=true \
        --set alertmanager.persistence.size=2Gi
    
    success "Prometheus Operator installed"
}

# Configure application metrics
configure_app_metrics() {
    log "Configuring application metrics..."
    
    # Create ServiceMonitor for backend
    kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: motionmath-backend-metrics
  namespace: $NAMESPACE
  labels:
    app: motionmath-backend
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: motionmath-frontend-metrics
  namespace: $NAMESPACE
  labels:
    app: motionmath-frontend
spec:
  selector:
    matchLabels:
      app: frontend
  endpoints:
  - port: metrics
    interval: 30s
    path: /api/metrics
EOF
    
    success "Application metrics configured"
}

# Configure database monitoring
configure_database_monitoring() {
    log "Configuring database monitoring..."
    
    # Deploy PostgreSQL Exporter
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
  namespace: $NAMESPACE
  labels:
    app: postgres-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-exporter
  template:
    metadata:
      labels:
        app: postgres-exporter
    spec:
      containers:
      - name: postgres-exporter
        image: wrouesnel/postgres_exporter:latest
        env:
        - name: DATA_SOURCE_NAME
          value: "postgresql://motionmath:$(kubectl get secret motionmath-secrets -n $NAMESPACE -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d)@postgres-service:5432/motionmath?sslmode=disable"
        ports:
        - containerPort: 9187
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-exporter
  namespace: $NAMESPACE
  labels:
    app: postgres-exporter
spec:
  selector:
    app: postgres-exporter
  ports:
  - port: 9187
    targetPort: 9187
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: postgres-exporter-metrics
  namespace: $NAMESPACE
spec:
  selector:
    matchLabels:
      app: postgres-exporter
  endpoints:
  - port: 9187
    interval: 30s
EOF
    
    success "Database monitoring configured"
}

# Configure Redis monitoring
configure_redis_monitoring() {
    log "Configuring Redis monitoring..."
    
    # Deploy Redis Exporter
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-exporter
  namespace: $NAMESPACE
  labels:
    app: redis-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-exporter
  template:
    metadata:
      labels:
        app: redis-exporter
    spec:
      containers:
      - name: redis-exporter
        image: oliver006/redis_exporter:latest
        env:
        - name: REDIS_ADDR
          value: "redis://redis-service:6379"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: motionmath-secrets
              key: REDIS_PASSWORD
        ports:
        - containerPort: 9121
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-exporter
  namespace: $NAMESPACE
  labels:
    app: redis-exporter
spec:
  selector:
    app: redis-exporter
  ports:
  - port: 9121
    targetPort: 9121
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: redis-exporter-metrics
  namespace: $NAMESPACE
spec:
  selector:
    matchLabels:
      app: redis-exporter
  endpoints:
  - port: 9121
    interval: 30s
EOF
    
    success "Redis monitoring configured"
}

# Configure custom alerts
configure_alerts() {
    log "Configuring custom alerts..."
    
    kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: motionmath-alerts
  namespace: $MONITORING_NAMESPACE
  labels:
    app: motionmath
spec:
  groups:
  - name: motionmath.rules
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.instance }}"
    
    - alert: HighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ $value }}s for {{ $labels.instance }}"
    
    - alert: DatabaseConnectionHigh
      expr: pg_stat_activity_count > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High database connections"
        description: "Database has {{ $value }} active connections"
    
    - alert: RedisMemoryHigh
      expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Redis memory usage high"
        description: "Redis memory usage is {{ $value | humanizePercentage }}"
    
    - alert: PodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Pod is crash looping"
        description: "Pod {{ $labels.pod }} is crash looping"
    
    - alert: HighCPUUsage
      expr: rate(container_cpu_usage_seconds_total[5m]) * 100 > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage"
        description: "CPU usage is {{ $value }}% for {{ $labels.pod }}"
    
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes / container_spec_memory_limit_bytes * 100 > 90
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High memory usage"
        description: "Memory usage is {{ $value }}% for {{ $labels.pod }}"
    
    - alert: DiskSpaceLow
      expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Low disk space"
        description: "Disk space is {{ $value }}% full on {{ $labels.instance }}"
    
    - alert: ServiceDown
      expr: up == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Service is down"
        description: "Service {{ $labels.instance }} is down"
    
    - alert: HPAAtMaxCapacity
      expr: kube_hpa_status_current_replicas == kube_hpa_status_max_replicas
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "HPA at maximum capacity"
        description: "HPA {{ $labels.hpa }} is at maximum capacity"
EOF
    
    success "Custom alerts configured"
}

# Configure Grafana dashboards
configure_grafana_dashboards() {
    log "Configuring Grafana dashboards..."
    
    # Create ConfigMap for dashboards
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: motionmath-dashboards
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
data:
  motionmath-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "MotionMath AI Overview",
        "tags": ["motionmath"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total[5m])",
                "legendFormat": "{{instance}}"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
                "legendFormat": "Error Rate"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
          },
          {
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
          },
          {
            "title": "Database Connections",
            "type": "graph",
            "targets": [
              {
                "expr": "pg_stat_activity_count",
                "legendFormat": "Active Connections"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
  motionmath-database.json: |
    {
      "dashboard": {
        "id": null,
        "title": "MotionMath AI Database",
        "tags": ["motionmath", "database"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Database Connections",
            "type": "graph",
            "targets": [
              {
                "expr": "pg_stat_activity_count",
                "legendFormat": "Active Connections"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
          },
          {
            "title": "Database Size",
            "type": "graph",
            "targets": [
              {
                "expr": "pg_database_size_bytes",
                "legendFormat": "{{datname}}"
              }
            ],
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
          },
          {
            "title": "Query Performance",
            "type": "table",
            "targets": [
              {
                "expr": "pg_stat_statements_mean_time_seconds",
                "legendFormat": "Mean Query Time"
              }
            ],
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
EOF
    
    success "Grafana dashboards configured"
}

# Configure alert routing
configure_alert_routing() {
    log "Configuring alert routing..."
    
    # Configure AlertManager
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-main
  namespace: $MONITORING_NAMESPACE
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      smtp_smarthost: 'smtp.sendgrid.net:587'
      smtp_from: 'alerts@motionmath.ai'
      smtp_auth_username: 'apikey'
      smtp_auth_password: 'YOUR_SENDGRID_API_KEY'
    
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
      - match:
          severity: warning
        receiver: 'warning-alerts'
    
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://127.0.0.1:5001/'
    
    - name: 'critical-alerts'
      email_configs:
      - to: 'devops@motionmath.ai'
        subject: '[CRITICAL] MotionMath AI Alert'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
      slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
    - name: 'warning-alerts'
      email_configs:
      - to: 'devops@motionmath.ai'
        subject: '[WARNING] MotionMath AI Alert'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
      slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#warnings'
        title: 'Warning Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
    inhibit_rules:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['alertname', 'dev', 'instance']
EOF
    
    success "Alert routing configured"
}

# Verify monitoring setup
verify_monitoring() {
    log "Verifying monitoring setup..."
    
    # Check Prometheus
    if kubectl get pods -n "$MONITORING_NAMESPACE" | grep -q "prometheus"; then
        success "Prometheus is running"
    else
        warning "Prometheus may not be properly configured"
    fi
    
    # Check Grafana
    if kubectl get pods -n "$MONITORING_NAMESPACE" | grep -q "grafana"; then
        success "Grafana is running"
    else
        warning "Grafana may not be properly configured"
    fi
    
    # Check AlertManager
    if kubectl get pods -n "$MONITORING_NAMESPACE" | grep -q "alertmanager"; then
        success "AlertManager is running"
    else
        warning "AlertManager may not be properly configured"
    fi
    
    success "Monitoring verification completed"
}

# Main function
main() {
    log "Starting monitoring setup for MotionMath AI..."
    
    # Install monitoring components
    install_prometheus_operator
    configure_app_metrics
    configure_database_monitoring
    configure_redis_monitoring
    configure_alerts
    configure_grafana_dashboards
    configure_alert_routing
    
    # Verify setup
    verify_monitoring
    
    success "Monitoring setup completed successfully!"
    
    log "Monitoring setup summary:"
    log "- Prometheus: Installed"
    log "- Grafana: Installed"
    log "- AlertManager: Installed"
    log "- Application Metrics: Configured"
    log "- Database Monitoring: Configured"
    log "- Redis Monitoring: Configured"
    log "- Custom Alerts: Configured"
    log "- Grafana Dashboards: Configured"
    log "- Alert Routing: Configured"
    
    log "Access URLs:"
    log "- Prometheus: http://prometheus.$MONITORING_NAMESPACE.svc.cluster.local:9090"
    log "- Grafana: http://grafana.$MONITORING_NAMESPACE.svc.cluster.local:3000"
    log "- AlertManager: http://alertmanager.$MONITORING_NAMESPACE.svc.cluster.local:9093"
}

# Run main function
main "$@"
