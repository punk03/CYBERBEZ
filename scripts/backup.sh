#!/bin/bash

# Backup script for PROKVANT system
# This script creates backups of databases and configuration

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/prokvant}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="prokvant_backup_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

log_info "Starting backup process..."

# Backup PostgreSQL
log_info "Backing up PostgreSQL..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST:-localhost}" \
    -U "${POSTGRES_USER:-prokvant}" \
    -d "${POSTGRES_DB:-prokvant_db}" \
    -F c \
    -f "${BACKUP_DIR}/${BACKUP_PREFIX}_postgresql.dump" || {
    log_error "PostgreSQL backup failed"
    exit 1
}

# Backup MongoDB
log_info "Backing up MongoDB..."
mongodump \
    --host="${MONGO_HOST:-localhost}:${MONGO_PORT:-27017}" \
    --username="${MONGO_USER:-prokvant}" \
    --password="${MONGO_PASSWORD:-prokvant_password}" \
    --authenticationDatabase=admin \
    --db="${MONGO_DB:-prokvant_logs}" \
    --out="${BACKUP_DIR}/${BACKUP_PREFIX}_mongodb" || {
    log_error "MongoDB backup failed"
    exit 1
}

# Backup configuration files
log_info "Backing up configuration..."
CONFIG_BACKUP="${BACKUP_DIR}/${BACKUP_PREFIX}_config.tar.gz"
tar -czf "${CONFIG_BACKUP}" \
    config/ \
    .env \
    2>/dev/null || log_warn "Some config files not found"

# Backup ML models
log_info "Backing up ML models..."
if [ -d "ml_models" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_PREFIX}_ml_models.tar.gz" ml_models/ || {
        log_warn "ML models backup failed"
    }
fi

# Create backup manifest
log_info "Creating backup manifest..."
cat > "${BACKUP_DIR}/${BACKUP_PREFIX}_manifest.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "backup_type": "full",
    "components": {
        "postgresql": "${BACKUP_PREFIX}_postgresql.dump",
        "mongodb": "${BACKUP_PREFIX}_mongodb",
        "config": "${BACKUP_PREFIX}_config.tar.gz",
        "ml_models": "${BACKUP_PREFIX}_ml_models.tar.gz"
    },
    "version": "0.1.0"
}
EOF

# Compress backup
log_info "Compressing backup..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_PREFIX}.tar.gz" \
    "${BACKUP_PREFIX}_postgresql.dump" \
    "${BACKUP_PREFIX}_mongodb" \
    "${BACKUP_PREFIX}_config.tar.gz" \
    "${BACKUP_PREFIX}_ml_models.tar.gz" \
    "${BACKUP_PREFIX}_manifest.json" 2>/dev/null || {
    log_warn "Compression failed, keeping individual files"
}

# Cleanup individual files if compression succeeded
if [ -f "${BACKUP_PREFIX}.tar.gz" ]; then
    rm -rf "${BACKUP_PREFIX}_postgresql.dump" \
           "${BACKUP_PREFIX}_mongodb" \
           "${BACKUP_PREFIX}_config.tar.gz" \
           "${BACKUP_PREFIX}_ml_models.tar.gz" \
           "${BACKUP_PREFIX}_manifest.json"
    log_info "Backup compressed: ${BACKUP_PREFIX}.tar.gz"
fi

# Cleanup old backups (keep last 7 days)
log_info "Cleaning up old backups..."
find "${BACKUP_DIR}" -name "prokvant_backup_*.tar.gz" -mtime +7 -delete || true

log_info "Backup completed successfully!"
log_info "Backup location: ${BACKUP_DIR}/${BACKUP_PREFIX}.tar.gz"
