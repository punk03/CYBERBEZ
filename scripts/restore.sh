#!/bin/bash

# Restore script for PROKVANT system

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/prokvant}"
BACKUP_FILE="${1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [ -z "${BACKUP_FILE}" ]; then
    log_error "Usage: $0 <backup_file>"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

log_info "Starting restore process from: ${BACKUP_FILE}"

# Extract backup
TEMP_DIR=$(mktemp -d)
log_info "Extracting backup..."
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}" || {
    log_error "Failed to extract backup"
    exit 1
}

# Find manifest
MANIFEST=$(find "${TEMP_DIR}" -name "*_manifest.json" | head -1)
if [ -z "${MANIFEST}" ]; then
    log_error "Manifest not found in backup"
    exit 1
fi

BACKUP_PREFIX=$(basename "${MANIFEST}" _manifest.json)

# Restore PostgreSQL
log_info "Restoring PostgreSQL..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
    -h "${POSTGRES_HOST:-localhost}" \
    -U "${POSTGRES_USER:-prokvant}" \
    -d "${POSTGRES_DB:-prokvant_db}" \
    --clean \
    --if-exists \
    "${TEMP_DIR}/${BACKUP_PREFIX}_postgresql.dump" || {
    log_error "PostgreSQL restore failed"
    exit 1
}

# Restore MongoDB
log_info "Restoring MongoDB..."
mongorestore \
    --host="${MONGO_HOST:-localhost}:${MONGO_PORT:-27017}" \
    --username="${MONGO_USER:-prokvant}" \
    --password="${MONGO_PASSWORD:-prokvant_password}" \
    --authenticationDatabase=admin \
    --db="${MONGO_DB:-prokvant_logs}" \
    --drop \
    "${TEMP_DIR}/${BACKUP_PREFIX}_mongodb/${MONGO_DB:-prokvant_logs}" || {
    log_error "MongoDB restore failed"
    exit 1
}

# Restore configuration
log_info "Restoring configuration..."
if [ -f "${TEMP_DIR}/${BACKUP_PREFIX}_config.tar.gz" ]; then
    tar -xzf "${TEMP_DIR}/${BACKUP_PREFIX}_config.tar.gz" -C . || {
        log_warn "Configuration restore failed"
    }
fi

# Restore ML models
log_info "Restoring ML models..."
if [ -f "${TEMP_DIR}/${BACKUP_PREFIX}_ml_models.tar.gz" ]; then
    tar -xzf "${TEMP_DIR}/${BACKUP_PREFIX}_ml_models.tar.gz" || {
        log_warn "ML models restore failed"
    }
fi

# Cleanup
rm -rf "${TEMP_DIR}"

log_info "Restore completed successfully!"
