#!/bin/bash
# Production deployment script for MotionMath AI
# This script handles secure deployment with rollback capabilities

set -euo pipefail

# Configuration
PROJECT_NAME="motionmath"
NAMESPACE="motionmath-prod"
BACKUP_DIR="/tmp/motionmath-backups"
LOG_FILE="/var/log/motionmath-deploy.log"
HEALTH_CHECK_URL="https://motionmath.ai/health"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"

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

# Send notification to Slack
notify_slack() {
    local message="$1"
    local color="${2:-good}"
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\",\"color\":\"$color\"}" \
            "$SLACK_WEBHOOK" || true
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    # Check current deployments
    log "Current deployment status:"
    kubectl get deployments -n "$NAMESPACE" || true
    
    success "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup current deployments
    kubectl get deployments -n "$NAMESPACE" -o yaml > "$backup_path/deployments.yaml"
    kubectl get services -n "$NAMESPACE" -o yaml > "$backup_path/services.yaml"
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_path/configmaps.yaml"
    kubectl get secrets -n "$NAMESPACE" -o yaml > "$backup_path/secrets.yaml"
    
    # Backup database
    log "Creating database backup..."
    kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        pg_dump -U motionmath motionmath > "$backup_path/database.sql"
    
    success "Backup created: $backup_name"
    echo "$backup_name" > "$BACKUP_DIR/latest-backup"
}

# Deploy application
deploy_application() {
    log "Starting deployment..."
    
    # Apply Kubernetes manifests
    log "Applying namespace and network policies..."
    kubectl apply -f infrastructure/kubernetes/namespace-enhanced.yaml
    
    log "Applying secrets and configmaps..."
    kubectl apply -f infrastructure/kubernetes/secrets-enhanced.yaml
    kubectl apply -f infrastructure/kubernetes/configmap-enhanced.yaml
    
    log "Deploying database..."
    kubectl apply -f infrastructure/kubernetes/database-enhanced.yaml
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s
    
    log "Deploying Redis..."
    kubectl apply -f infrastructure/kubernetes/redis.yaml
    
    # Wait for Redis to be ready
    log "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s
    
    log "Deploying backend services..."
    kubectl apply -f infrastructure/kubernetes/backend.yaml
    
    # Wait for backend to be ready
    log "Waiting for backend to be ready..."
    kubectl wait --for=condition=available deployment/backend-deployment -n "$NAMESPACE" --timeout=600s
    
    log "Deploying frontend services..."
    kubectl apply -f infrastructure/kubernetes/frontend.yaml
    
    # Wait for frontend to be ready
    log "Waiting for frontend to be ready..."
    kubectl wait --for=condition=available deployment/frontend-deployment -n "$NAMESPACE" --timeout=600s
    
    log "Applying ingress and HPA..."
    kubectl apply -f infrastructure/kubernetes/ingress-enhanced.yaml
    kubectl apply -f infrastructure/kubernetes/hpa-enhanced.yaml
    
    success "Deployment completed"
}

# Health checks
health_checks() {
    log "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed"
        sleep 10
        ((attempt++))
    done
    
    error "Health checks failed after $max_attempts attempts"
    return 1
}

# Rollback function
rollback() {
    local backup_name="${1:-$(cat "$BACKUP_DIR/latest-backup" 2>/dev/null)}"
    
    if [[ -z "$backup_name" ]]; then
        error "No backup found for rollback"
        exit 1
    fi
    
    warning "Starting rollback to backup: $backup_name"
    
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    # Restore deployments
    kubectl apply -f "$backup_path/deployments.yaml" --force
    kubectl apply -f "$backup_path/services.yaml" --force
    kubectl apply -f "$backup_path/configmaps.yaml" --force
    kubectl apply -f "$backup_path/secrets.yaml" --force
    
    # Restore database
    if [[ -f "$backup_path/database.sql" ]]; then
        log "Restoring database..."
        kubectl exec -i -n "$NAMESPACE" deployment/postgres -- \
            psql -U motionmath motionmath < "$backup_path/database.sql"
    fi
    
    success "Rollback completed"
    notify_slack "🔄 MotionMath AI rollback completed: $backup_name" "warning"
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -type d -name "backup-*" -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    success "Backup cleanup completed"
}

# Post-deployment verification
post_deployment_verification() {
    log "Running post-deployment verification..."
    
    # Check pod status
    log "Checking pod status..."
    kubectl get pods -n "$NAMESPACE"
    
    # Check service status
    log "Checking service status..."
    kubectl get services -n "$NAMESPACE"
    
    # Check HPA status
    log "Checking HPA status..."
    kubectl get hpa -n "$NAMESPACE"
    
    # Check ingress status
    log "Checking ingress status..."
    kubectl get ingress -n "$NAMESPACE"
    
    success "Post-deployment verification completed"
}

# Main deployment function
main() {
    log "Starting MotionMath AI deployment..."
    
    # Check for rollback flag
    if [[ "${1:-}" == "--rollback" ]]; then
        rollback "${2:-}"
        exit 0
    fi
    
    # Check for dry-run flag
    if [[ "${1:-}" == "--dry-run" ]]; then
        log "Running dry-run deployment..."
        kubectl apply --dry-run=client -f infrastructure/kubernetes/
        success "Dry-run completed"
        exit 0
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Run deployment pipeline
    pre_deployment_checks
    create_backup
    deploy_application
    health_checks
    post_deployment_verification
    cleanup_backups
    
    success "MotionMath AI deployment completed successfully!"
    notify_slack "🚀 MotionMath AI deployment completed successfully!" "good"
    
    log "Deployment summary:"
    log "- Namespace: $NAMESPACE"
    log "- Backup: $(cat "$BACKUP_DIR/latest-backup")"
    log "- Health check: $HEALTH_CHECK_URL"
}

# Handle script interruption
trap 'error "Deployment interrupted"; notify_slack "❌ MotionMath AI deployment interrupted" "danger"; exit 1' INT TERM

# Run main function
main "$@"
