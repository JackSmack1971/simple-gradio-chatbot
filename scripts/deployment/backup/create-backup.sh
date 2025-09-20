#!/bin/bash

# Backup Creation Script for Personal AI Chatbot
# Creates comprehensive backups of application data and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message"
}

# Detect platform
detect_platform() {
    case "$(uname -s)" in
        Linux*)     PLATFORM=linux ;;
        Darwin*)    PLATFORM=macos ;;
        CYGWIN*|MINGW*|MSYS*) PLATFORM=windows ;;
        *)          PLATFORM=unknown ;;
    esac
    log "INFO" "Detected platform: $PLATFORM"
}

# Get data directory
get_data_dir() {
    if [[ -n "$DATA_DIR" ]]; then
        echo "$DATA_DIR"
    elif [[ "$PLATFORM" == "linux" ]]; then
        echo "$HOME/.local/share/personal-ai-chatbot"
    elif [[ "$PLATFORM" == "macos" ]]; then
        echo "$HOME/Library/Application Support/PersonalAIChatbot"
    elif [[ "$PLATFORM" == "windows" ]]; then
        echo "$APPDATA/PersonalAIChatbot"
    else
        echo "./data"
    fi
}

# Create backup filename
create_backup_filename() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_type="$1"
    echo "personal-ai-chatbot-${backup_type}-${timestamp}"
}

# Create data backup
create_data_backup() {
    local data_dir="$1"
    local backup_dir="$2"
    local backup_name="$3"

    log "INFO" "Creating data backup..."

    # Create backup directory
    local backup_path="$backup_dir/${backup_name}-data"
    mkdir -p "$backup_path"

    # Copy data directories
    local dirs_to_backup=("conversations" "config" "logs")
    for dir_name in "${dirs_to_backup[@]}"; do
        if [[ -d "$data_dir/$dir_name" ]]; then
            cp -r "$data_dir/$dir_name" "$backup_path/"
            log "INFO" "✓ Backed up $dir_name directory"
        else
            log "WARNING" "Directory $dir_name not found, skipping"
        fi
    done

    # Create backup manifest
    cat > "$backup_path/backup-manifest.txt" << EOF
Personal AI Chatbot Data Backup
Created: $(date)
Platform: $PLATFORM
Data Directory: $data_dir
Backup Type: data

Contents:
$(find "$backup_path" -type f | wc -l) files
$(du -sh "$backup_path" | cut -f1) total size

Directories included:
$(ls -la "$backup_path" | grep ^d | awk '{print $9}' | grep -v '^\.$' | grep -v '^\.\.$' | tr '\n' ' ')
EOF

    # Create compressed archive
    local archive_name="${backup_name}-data.tar.gz"
    cd "$backup_dir"
    tar -czf "$archive_name" "${backup_name}-data"

    # Clean up uncompressed backup
    rm -rf "${backup_name}-data"

    log "INFO" "✓ Data backup created: $backup_dir/$archive_name"
    echo "$backup_dir/$archive_name"
}

# Create configuration backup
create_config_backup() {
    local data_dir="$1"
    local backup_dir="$2"
    local backup_name="$3"

    log "INFO" "Creating configuration backup..."

    # Create backup directory
    local backup_path="$backup_dir/${backup_name}-config"
    mkdir -p "$backup_path"

    # Copy configuration files
    local config_files=(
        "$data_dir/config/app_config.json"
        "$data_dir/.env"
        "$data_dir/.env.local"
    )

    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            # Create sanitized copy (remove sensitive data)
            local filename=$(basename "$config_file")
            if [[ "$filename" == ".env"* ]]; then
                # For .env files, create a template version
                sed 's/=.*/=REDACTED/' "$config_file" > "$backup_path/$filename.template"
                log "INFO" "✓ Created sanitized $filename template"
            else
                cp "$config_file" "$backup_path/"
                log "INFO" "✓ Backed up $filename"
            fi
        fi
    done

    # Backup application files (optional)
    if [[ "$FULL_BACKUP" == "true" ]]; then
        log "INFO" "Creating full application backup..."
        # This would backup the entire application directory
        # For now, just backup key files
        mkdir -p "$backup_path/app"
        find . -name "*.py" -type f | head -10 | xargs -I {} cp {} "$backup_path/app/" 2>/dev/null || true
    fi

    # Create backup manifest
    cat > "$backup_path/backup-manifest.txt" << EOF
Personal AI Chatbot Configuration Backup
Created: $(date)
Platform: $PLATFORM
Data Directory: $data_dir
Backup Type: config

Contents:
$(find "$backup_path" -type f | wc -l) files
$(du -sh "$backup_path" | cut -f1) total size

Configuration files included:
$(ls -la "$backup_path" | grep -v ^d | awk '{print $9}' | tr '\n' ' ')
EOF

    # Create compressed archive
    local archive_name="${backup_name}-config.tar.gz"
    cd "$backup_dir"
    tar -czf "$archive_name" "${backup_name}-config"

    # Clean up uncompressed backup
    rm -rf "${backup_name}-config"

    log "INFO" "✓ Configuration backup created: $backup_dir/$archive_name"
    echo "$backup_dir/$archive_name"
}

# Create encrypted backup
create_encrypted_backup() {
    local data_dir="$1"
    local backup_dir="$2"
    local backup_name="$3"

    log "INFO" "Creating encrypted backup..."

    # Check if encryption tools are available
    if ! command -v openssl &> /dev/null; then
        log "WARNING" "OpenSSL not found, skipping encrypted backup"
        return 1
    fi

    # Create temporary backup
    local temp_backup="$backup_dir/${backup_name}-temp.tar.gz"
    local encrypted_backup="$backup_dir/${backup_name}-encrypted.tar.gz.enc"

    # First create a regular backup
    create_data_backup "$data_dir" "$backup_dir" "${backup_name}-data" > /dev/null
    local data_backup="$backup_dir/${backup_name}-data.tar.gz"

    if [[ -f "$data_backup" ]]; then
        # Encrypt the backup
        openssl enc -aes-256-cbc -salt -in "$data_backup" -out "$encrypted_backup" -k "${ENCRYPTION_PASSWORD:-default_password}"

        # Clean up unencrypted backup
        rm "$data_backup"

        log "INFO" "✓ Encrypted backup created: $encrypted_backup"
        echo "$encrypted_backup"
    else
        log "ERROR" "Failed to create data backup for encryption"
        return 1
    fi
}

# Clean old backups
clean_old_backups() {
    local backup_dir="$1"
    local max_backups="${MAX_BACKUPS:-7}"

    log "INFO" "Cleaning old backups (keeping last $max_backups)..."

    # Find and sort backup files by modification time
    local backup_files=($(find "$backup_dir" -name "personal-ai-chatbot-*.tar.gz*" -type f -printf '%T@ %p\n' | sort -n | cut -d' ' -f2-))

    if [[ ${#backup_files[@]} -gt $max_backups ]]; then
        local files_to_delete=$(( ${#backup_files[@]} - $max_backups ))
        log "INFO" "Deleting $files_to_delete old backup(s)..."

        for ((i=0; i<files_to_delete; i++)); do
            rm "${backup_files[$i]}"
            log "INFO" "✓ Deleted old backup: ${backup_files[$i]}"
        done
    else
        log "INFO" "No old backups to clean"
    fi
}

# Main backup function
main() {
    # Parse command line arguments
    BACKUP_TYPE="full"
    ENCRYPTED=false
    FULL_BACKUP=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            --encrypted)
                ENCRYPTED=true
                shift
                ;;
            --full)
                FULL_BACKUP=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--type TYPE] [--encrypted] [--full]"
                echo "Types: data, config, full"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    log "INFO" "Starting backup creation..."
    log "INFO" "Backup type: $BACKUP_TYPE"
    log "INFO" "Encrypted: $ENCRYPTED"

    detect_platform
    local data_dir=$(get_data_dir)
    local backup_dir="$data_dir/backups"

    # Create backup directory
    mkdir -p "$backup_dir"

    # Generate backup name
    local backup_name=$(create_backup_filename "$BACKUP_TYPE")

    # Create backups based on type
    local created_backups=()

    case $BACKUP_TYPE in
        data)
            local backup_file=$(create_data_backup "$data_dir" "$backup_dir" "$backup_name")
            created_backups+=("$backup_file")
            ;;
        config)
            local backup_file=$(create_config_backup "$data_dir" "$backup_dir" "$backup_name")
            created_backups+=("$backup_file")
            ;;
        full)
            local data_backup=$(create_data_backup "$data_dir" "$backup_dir" "$backup_name")
            local config_backup=$(create_config_backup "$data_dir" "$backup_dir" "$backup_name")
            created_backups+=("$data_backup" "$config_backup")
            ;;
        *)
            log "ERROR" "Unknown backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # Create encrypted backups if requested
    if [[ "$ENCRYPTED" == "true" ]]; then
        log "INFO" "Creating encrypted backups..."
        for backup_file in "${created_backups[@]}"; do
            if [[ -f "$backup_file" ]]; then
                local encrypted_file=$(create_encrypted_backup "$data_dir" "$backup_dir" "$backup_name")
                if [[ -n "$encrypted_file" ]]; then
                    created_backups+=("$encrypted_file")
                fi
            fi
        done
    fi

    # Clean old backups
    clean_old_backups "$backup_dir"

    # Summary
    log "INFO" "Backup creation completed successfully!"
    echo
    echo -e "${GREEN}Backup Summary:${NC}"
    echo "Location: $backup_dir"
    echo "Created backups:"
    for backup_file in "${created_backups[@]}"; do
        if [[ -f "$backup_file" ]]; then
            local size=$(du -h "$backup_file" | cut -f1)
            echo "  ✓ $(basename "$backup_file") (${size})"
        fi
    done
    echo
    echo "Total backups in directory: $(find "$backup_dir" -name "personal-ai-chatbot-*.tar.gz*" | wc -l)"
}

# Run with error handling
trap 'log "ERROR" "Backup creation failed"' ERR

main "$@"