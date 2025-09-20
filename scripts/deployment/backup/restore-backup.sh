#!/bin/bash

# Backup Restoration Script for Personal AI Chatbot
# Restores application data and configuration from backups

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

# List available backups
list_backups() {
    local backup_dir="$1"

    if [[ ! -d "$backup_dir" ]]; then
        log "ERROR" "Backup directory not found: $backup_dir"
        return 1
    fi

    echo "Available backups in $backup_dir:"
    echo

    local backup_files=($(find "$backup_dir" -name "personal-ai-chatbot-*.tar.gz*" -type f -printf '%T@ %p\n' | sort -nr | cut -d' ' -f2-))

    if [[ ${#backup_files[@]} -eq 0 ]]; then
        echo "No backups found."
        return 1
    fi

    local count=1
    for backup_file in "${backup_files[@]}"; do
        local filename=$(basename "$backup_file")
        local size=$(du -h "$backup_file" | cut -f1)
        local modified=$(stat -c '%y' "$backup_file" 2>/dev/null || stat -f '%Sm' "$backup_file" 2>/dev/null || date)

        # Extract backup type and date from filename
        local backup_type=$(echo "$filename" | sed -n 's/personal-ai-chatbot-\([^-]*\)-.*/\1/p')
        local backup_date=$(echo "$filename" | sed -n 's/.*-\([0-9]\{8\}\)_[0-9]\{6\}.*/\1/p')

        if [[ -n "$backup_date" ]]; then
            # Format date as YYYY-MM-DD
            backup_date="${backup_date:0:4}-${backup_date:4:2}-${backup_date:6:2}"
        fi

        printf "%2d) %s\n" $count "$filename"
        printf "    Type: %s | Size: %s | Date: %s\n" "$backup_type" "$size" "$backup_date"
        printf "    Path: %s\n" "$backup_file"
        echo

        ((count++))
    done
}

# Select backup interactively
select_backup() {
    local backup_dir="$1"

    list_backups "$backup_dir"

    local backup_files=($(find "$backup_dir" -name "personal-ai-chatbot-*.tar.gz*" -type f -printf '%T@ %p\n' | sort -nr | cut -d' ' -f2-))

    if [[ ${#backup_files[@]} -eq 0 ]]; then
        log "ERROR" "No backups available for restoration"
        exit 1
    fi

    echo -n "Enter backup number to restore (1-${#backup_files[@]}): "
    read -r selection

    # Validate selection
    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [[ $selection -lt 1 ]] || [[ $selection -gt ${#backup_files[@]} ]]; then
        log "ERROR" "Invalid selection: $selection"
        exit 1
    fi

    # Get selected backup (arrays are 0-indexed)
    local selected_index=$((selection - 1))
    echo "${backup_files[$selected_index]}"
}

# Decrypt backup if needed
decrypt_backup() {
    local backup_file="$1"
    local temp_dir="$2"

    if [[ "$backup_file" == *.enc ]]; then
        log "INFO" "Backup is encrypted, decrypting..."

        if ! command -v openssl &> /dev/null; then
            log "ERROR" "OpenSSL required for decrypting backups"
            exit 1
        fi

        local decrypted_file="$temp_dir/$(basename "$backup_file" .enc)"

        # Prompt for decryption password
        echo -n "Enter decryption password: "
        read -rs password
        echo

        if ! openssl enc -d -aes-256-cbc -in "$backup_file" -out "$decrypted_file" -k "$password"; then
            log "ERROR" "Failed to decrypt backup"
            rm -f "$decrypted_file"
            exit 1
        fi

        log "INFO" "✓ Backup decrypted successfully"
        echo "$decrypted_file"
    else
        echo "$backup_file"
    fi
}

# Extract backup
extract_backup() {
    local backup_file="$1"
    local extract_dir="$2"

    log "INFO" "Extracting backup: $(basename "$backup_file")"

    if ! tar -tzf "$backup_file" &> /dev/null; then
        log "ERROR" "Invalid or corrupted backup file"
        exit 1
    fi

    mkdir -p "$extract_dir"
    if ! tar -xzf "$backup_file" -C "$extract_dir"; then
        log "ERROR" "Failed to extract backup"
        exit 1
    fi

    log "INFO" "✓ Backup extracted to: $extract_dir"

    # List extracted contents
    local extracted_dir="$extract_dir/$(basename "$backup_file" .tar.gz)"
    if [[ -d "$extracted_dir" ]]; then
        echo "Extracted contents:"
        find "$extracted_dir" -type f | head -10
        if [[ $(find "$extracted_dir" -type f | wc -l) -gt 10 ]]; then
            echo "... and $(($(find "$extracted_dir" -type f | wc -l) - 10)) more files"
        fi
        echo "$extracted_dir"
    else
        log "ERROR" "Extraction directory not found"
        exit 1
    fi
}

# Validate backup contents
validate_backup() {
    local backup_dir="$1"
    local backup_type="$2"

    log "INFO" "Validating backup contents..."

    case $backup_type in
        data)
            local required_items=("conversations" "config" "logs")
            for item in "${required_items[@]}"; do
                if [[ ! -d "$backup_dir/$item" ]] && [[ ! -f "$backup_dir/$item" ]]; then
                    log "WARNING" "Expected item not found in backup: $item"
                fi
            done
            ;;
        config)
            local config_files=("app_config.json")
            for config_file in "${config_files[@]}"; do
                if [[ ! -f "$backup_dir/config/$config_file" ]]; then
                    log "WARNING" "Configuration file not found: $config_file"
                fi
            done
            ;;
    esac

    # Check for manifest file
    if [[ -f "$backup_dir/backup-manifest.txt" ]]; then
        log "INFO" "✓ Backup manifest found"
        cat "$backup_dir/backup-manifest.txt"
    else
        log "WARNING" "Backup manifest not found"
    fi
}

# Restore data
restore_data() {
    local backup_dir="$1"
    local data_dir="$2"
    local dry_run="${3:-false}"

    log "INFO" "Restoring data from backup..."

    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "DRY RUN - No files will be modified"
    fi

    # Create data directory if it doesn't exist
    if [[ ! -d "$data_dir" ]]; then
        if [[ "$dry_run" != "true" ]]; then
            mkdir -p "$data_dir"
        fi
        log "INFO" "✓ Created data directory: $data_dir"
    fi

    # Restore directories
    local dirs_to_restore=("conversations" "config" "logs")
    for dir_name in "${dirs_to_restore[@]}"; do
        if [[ -d "$backup_dir/$dir_name" ]]; then
            if [[ "$dry_run" == "true" ]]; then
                log "INFO" "[DRY RUN] Would restore directory: $dir_name"
                find "$backup_dir/$dir_name" -type f | wc -l | xargs printf "  %d files in %s\n" | log "INFO"
            else
                # Create backup of existing directory
                if [[ -d "$data_dir/$dir_name" ]]; then
                    local backup_suffix=".backup.$(date '+%Y%m%d_%H%M%S')"
                    mv "$data_dir/$dir_name" "$data_dir/$dir_name$backup_suffix"
                    log "INFO" "✓ Backed up existing $dir_name to ${dir_name}${backup_suffix}"
                fi

                cp -r "$backup_dir/$dir_name" "$data_dir/"
                log "INFO" "✓ Restored directory: $dir_name"
            fi
        else
            log "WARNING" "Directory not found in backup: $dir_name"
        fi
    done

    # Restore individual files
    local files_to_restore=("$backup_dir/.env.template")
    for file_path in "${files_to_restore[@]}"; do
        if [[ -f "$file_path" ]]; then
            local filename=$(basename "$file_path")
            if [[ "$dry_run" == "true" ]]; then
                log "INFO" "[DRY RUN] Would restore file: $filename"
            else
                cp "$file_path" "$data_dir/"
                log "INFO" "✓ Restored file: $filename"
            fi
        fi
    done
}

# Main restoration function
main() {
    # Parse command line arguments
    BACKUP_FILE=""
    DRY_RUN=false
    INTERACTIVE=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup-file)
                BACKUP_FILE="$2"
                INTERACTIVE=false
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--backup-file FILE] [--dry-run]"
                echo "  --backup-file FILE: Specify backup file to restore"
                echo "  --dry-run: Show what would be restored without making changes"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    log "INFO" "Starting backup restoration..."
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN MODE - No changes will be made"
    fi

    detect_platform
    local data_dir=$(get_data_dir)
    local backup_dir="$data_dir/backups"
    local temp_dir="/tmp/personal-ai-chatbot-restore-$(date '+%s')"

    # Clean up temp directory on exit
    trap "rm -rf '$temp_dir'" EXIT

    # Select backup file
    if [[ -z "$BACKUP_FILE" ]]; then
        if [[ "$INTERACTIVE" == "true" ]]; then
            BACKUP_FILE=$(select_backup "$backup_dir")
        else
            log "ERROR" "Backup file not specified. Use --backup-file option."
            exit 1
        fi
    fi

    if [[ ! -f "$BACKUP_FILE" ]]; then
        log "ERROR" "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    log "INFO" "Selected backup: $(basename "$BACKUP_FILE")"

    # Handle encrypted backups
    local actual_backup_file=$(decrypt_backup "$BACKUP_FILE" "$temp_dir")

    # Extract backup
    mkdir -p "$temp_dir/extracted"
    local extracted_dir=$(extract_backup "$actual_backup_file" "$temp_dir/extracted")

    # Find the actual backup content directory
    local content_dir="$temp_dir/extracted/$(basename "$actual_backup_file" .tar.gz)"
    if [[ ! -d "$content_dir" ]]; then
        # Try to find any directory in extracted
        content_dir=$(find "$temp_dir/extracted" -mindepth 1 -maxdepth 1 -type d | head -1)
    fi

    if [[ ! -d "$content_dir" ]]; then
        log "ERROR" "Could not find backup content directory"
        exit 1
    fi

    # Determine backup type from content
    local backup_type="unknown"
    if [[ -d "$content_dir/conversations" ]] && [[ -d "$content_dir/config" ]]; then
        backup_type="data"
    elif [[ -d "$content_dir/config" ]] && [[ ! -d "$content_dir/conversations" ]]; then
        backup_type="config"
    fi

    log "INFO" "Detected backup type: $backup_type"

    # Validate backup
    validate_backup "$content_dir" "$backup_type"

    # Confirm restoration
    if [[ "$DRY_RUN" != "true" ]] && [[ "$INTERACTIVE" == "true" ]]; then
        echo
        echo -e "${YELLOW}WARNING: This will overwrite existing data!${NC}"
        echo "Backup file: $(basename "$BACKUP_FILE")"
        echo "Data directory: $data_dir"
        echo
        echo -n "Continue with restoration? (y/N): "
        read -r confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log "INFO" "Restoration cancelled by user"
            exit 0
        fi
    fi

    # Perform restoration
    restore_data "$content_dir" "$data_dir" "$DRY_RUN"

    # Cleanup
    if [[ -f "$actual_backup_file" ]] && [[ "$actual_backup_file" != "$BACKUP_FILE" ]]; then
        rm -f "$actual_backup_file"
    fi

    log "INFO" "Backup restoration completed successfully!"
    if [[ "$DRY_RUN" != "true" ]]; then
        echo
        echo -e "${GREEN}Restoration completed!${NC}"
        echo "Data directory: $data_dir"
        echo
        echo "Next steps:"
        echo "1. Review restored files"
        echo "2. Update configuration if needed"
        echo "3. Restart the application"
    fi
}

# Run with error handling
trap 'log "ERROR" "Backup restoration failed"' ERR

main "$@"