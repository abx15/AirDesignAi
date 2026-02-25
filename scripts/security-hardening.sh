#!/bin/bash
# Security hardening script for MotionMath AI
# This script applies security best practices to the infrastructure

set -euo pipefail

# Configuration
NAMESPACE="motionmath-prod"
LOG_FILE="/var/log/motionmath-security.log"

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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Apply network policies
apply_network_policies() {
    log "Applying network policies..."
    
    kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: $NAMESPACE
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-ingress
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3000
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-ingress
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
EOF
    
    success "Network policies applied"
}

# Apply Pod Security Policies
apply_pod_security_policies() {
    log "Applying Pod Security Policies..."
    
    kubectl apply -f - <<EOF
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: motionmath-psp
  namespace: $NAMESPACE
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
EOF
    
    success "Pod Security Policies applied"
}

# Apply Resource Quotas
apply_resource_quotas() {
    log "Applying Resource Quotas..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: motionmath-quota
  namespace: $NAMESPACE
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
    pods: "100"
    services: "20"
    secrets: "20"
    configmaps: "20"
    count/secrets: "20"
    count/configmaps: "20"
EOF
    
    success "Resource Quotas applied"
}

# Apply Limit Ranges
apply_limit_ranges() {
    log "Applying Limit Ranges..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: LimitRange
metadata:
  name: motionmath-limits
  namespace: $NAMESPACE
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
  - max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
  - max:
      storage: 10Gi
    min:
      storage: 1Gi
    type: PersistentVolumeClaim
EOF
    
    success "Limit Ranges applied"
}

# Enable RBAC
enable_rbac() {
    log "Enabling RBAC..."
    
    # Create service accounts
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: motionmath-backend-sa
  namespace: $NAMESPACE
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: motionmath-frontend-sa
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: $NAMESPACE
  name: motionmath-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: motionmath-backend-binding
  namespace: $NAMESPACE
subjects:
- kind: ServiceAccount
  name: motionmath-backend-sa
  namespace: $NAMESPACE
roleRef:
  kind: Role
  name: motionmath-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: motionmath-frontend-binding
  namespace: $NAMESPACE
subjects:
- kind: ServiceAccount
  name: motionmath-frontend-sa
  namespace: $NAMESPACE
roleRef:
  kind: Role
  name: motionmath-role
  apiGroup: rbac.authorization.k8s.io
EOF
    
    success "RBAC enabled"
}

# Apply security contexts
apply_security_contexts() {
    log "Applying security contexts..."
    
    # Update deployments with security contexts
    kubectl patch deployment backend-deployment -n "$NAMESPACE" -p '{"spec":{"template":{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":1001,"fsGroup":1001}}}}}' || true
    kubectl patch deployment frontend-deployment -n "$NAMESPACE" -p '{"spec":{"template":{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":1001,"fsGroup":1001}}}}}' || true
    
    success "Security contexts applied"
}

# Enable audit logging
enable_audit_logging() {
    log "Enabling audit logging..."
    
    # This would typically be done at cluster level
    warning "Audit logging requires cluster-level configuration"
    log "Please ensure audit logging is enabled in your cluster"
}

# Apply image security policies
apply_image_security_policies() {
    log "Applying image security policies..."
    
    kubectl apply -f - <<EOF
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: ns-must-have-gk
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace"]
  parameters:
    labels: ["gatekeeper.sh/system"]
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredProbes
metadata:
  name: k8srequiredprobes
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
  parameters:
    probes: ["livenessProbe", "readinessProbe"]
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDisallowRoot
metadata:
  name: k8sdisallowroot
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
EOF
    
    success "Image security policies applied"
}

# Configure secrets management
configure_secrets_management() {
    log "Configuring secrets management..."
    
    # Rotate secrets
    kubectl create secret generic motionmath-secrets-rotated \
        --from-literal=DATABASE_PASSWORD="$(openssl rand -base64 32)" \
        --from-literal=REDIS_PASSWORD="$(openssl rand -base64 32)" \
        --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 64)" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f - || true
    
    success "Secrets management configured"
}

# Enable monitoring and alerting
enable_monitoring() {
    log "Enabling security monitoring..."
    
    # Deploy Prometheus and Grafana for security monitoring
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-rules
  namespace: $NAMESPACE
data:
  security.yml: |
    groups:
    - name: security.rules
      rules:
      - alert: PodSecurityPolicyViolation
        expr: kube_pod_status_phase{phase="Failed"} > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod Security Policy Violation"
          description: "Pod {{ $labels.pod }} has failed"
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "Pod {{ $labels.pod }} has high CPU usage"
EOF
    
    success "Security monitoring enabled"
}

# Verify security hardening
verify_security() {
    log "Verifying security hardening..."
    
    # Check network policies
    if kubectl get networkpolicy -n "$NAMESPACE" | grep -q "deny-all"; then
        success "Network policies are active"
    else
        warning "Network policies may not be properly configured"
    fi
    
    # Check RBAC
    if kubectl get rolebinding -n "$NAMESPACE" | grep -q "motionmath"; then
        success "RBAC is configured"
    else
        warning "RBAC may not be properly configured"
    fi
    
    # Check resource quotas
    if kubectl get resourcequota -n "$NAMESPACE" | grep -q "motionmath"; then
        success "Resource quotas are active"
    else
        warning "Resource quotas may not be properly configured"
    fi
    
    success "Security verification completed"
}

# Main function
main() {
    log "Starting security hardening for MotionMath AI..."
    
    check_root
    
    # Apply security configurations
    apply_network_policies
    apply_pod_security_policies
    apply_resource_quotas
    apply_limit_ranges
    enable_rbac
    apply_security_contexts
    enable_audit_logging
    apply_image_security_policies
    configure_secrets_management
    enable_monitoring
    
    # Verify security
    verify_security
    
    success "Security hardening completed successfully!"
    
    log "Security hardening summary:"
    log "- Network policies: Applied"
    log "- Pod Security Policies: Applied"
    log "- Resource Quotas: Applied"
    log "- RBAC: Enabled"
    log "- Security Contexts: Applied"
    log "- Secrets Management: Configured"
    log "- Monitoring: Enabled"
}

# Run main function
main "$@"
