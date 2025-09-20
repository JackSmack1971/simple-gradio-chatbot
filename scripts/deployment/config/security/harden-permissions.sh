#!/bin/bash

# Security Hardening Script - File Permissions
# This script sets secure file permissions for Personal AI Chatbot

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

# Secure directory permissions
secure_directory_permissions() {
    local data_dir="$1"
    log "INFO" "Securing directory permissions..."

    # Create data directory if it doesn't exist
    mkdir -p "$data_dir"

    # Secure main data directory (owner read/write/execute only)
    chmod 700 "$data_dir"
    log "INFO" "✓ Secured main data directory: $data_dir"

    # Secure subdirectories
    local subdirs=("config" "conversations" "backups" "logs" "cache")
    for subdir in "${subdirs[@]}"; do
        local full_path="$data_dir/$subdir"
        mkdir -p "$full_path"
        chmod 700 "$full_path"
        log "INFO" "✓ Secured subdirectory: $full_path"
    done
}

# Secure file permissions
secure_file_permissions() {
    local data_dir="$1"
    log "INFO" "Securing file permissions..."

    # Secure configuration files
    local config_files=(
        "$data_dir/config/app_config.json"
        "$data_dir/.env"
        "$data_dir/.env.local"
    )

    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            chmod 600 "$config_file"
            log "INFO" "✓ Secured config file: $config_file"
        fi
    done

    # Secure conversation files
    if [[ -d "$data_dir/conversations" ]]; then
        find "$data_dir/conversations" -type f -name "*.json" -exec chmod 600 {} \;
        log "INFO" "✓ Secured conversation files"
    fi

    # Secure backup files
    if [[ -d "$data_dir/backups" ]]; then
        find "$data_dir/backups" -type f \( -name "*.backup" -o -name "*.tar.gz" \) -exec chmod 600 {} \;
        log "INFO" "✓ Secured backup files"
    fi

    # Secure log files
    if [[ -d "$data_dir/logs" ]]; then
        find "$data_dir/logs" -type f -name "*.log" -exec chmod 600 {} \;
        log "INFO" "✓ Secured log files"
    fi
}

# Set ownership (Linux/macOS only)
set_ownership() {
    if [[ "$PLATFORM" == "windows" ]]; then
        return
    fi

    local data_dir="$1"
    log "INFO" "Setting file ownership..."

    # Set ownership to current user
    local current_user=$(whoami)
    local current_group=$(id -gn)

    chown -R "$current_user:$current_group" "$data_dir"
    log "INFO" "✓ Set ownership to $current_user:$current_group"
}

# Validate permissions
validate_permissions() {
    local data_dir="$1"
    log "INFO" "Validating permissions..."

    local issues_found=0

    # Check main directory
    local dir_perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%Lp" "$data_dir" 2>/dev/null)
    if [[ "$dir_perms" != "700" ]]; then
        log "WARNING" "Main directory permissions should be 700, got $dir_perms"
        issues_found=$((issues_found + 1))
    fi

    # Check config files
    local config_files=(
        "$data_dir/config/app_config.json"
        "$data_dir/.env"
    )

    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            local file_perms=$(stat -c "%a" "$config_file" 2>/dev/null || stat -f "%Lp" "$config_file" 2>/dev/null)
            if [[ "$file_perms" != "600" ]]; then
                log "WARNING" "Config file permissions should be 600, got $file_perms for $config_file"
                issues_found=$((issues_found + 1))
            fi
        fi
    done

    if [[ $issues_found -eq 0 ]]; then
        log "INFO" "✓ All permissions are secure"
    else
        log "WARNING" "Found $issues_found permission issues"
    fi

    return $issues_found
}

# Windows-specific permission hardening
windows_specific_hardening() {
    if [[ "$PLATFORM" != "windows" ]]; then
        return
    fi

    log "INFO" "Applying Windows-specific permission hardening..."

    local data_dir="$1"

    # Use icacls for Windows permissions
    if command -v icacls &> /dev/null; then
        # Remove inheritance and set explicit permissions
        icacls "$data_dir" /inheritance:r /grant:r "$USER:(OI)(CI)F" /T /Q

        # Remove permissions for other users
        icacls "$data_dir" /remove:g "Everyone" /T /Q 2>/dev/null || true
        icacls "$data_dir" /remove:g "Users" /T /Q 2>/dev/null || true

        log "INFO" "✓ Applied Windows ACL permissions"
    else
        log "WARNING" "icacls not available, skipping Windows-specific permissions"
    fi
}

# Main function
main() {
    log "INFO" "Starting file permission hardening..."

    detect_platform
    local data_dir=$(get_data_dir)

    log "INFO" "Using data directory: $data_dir"

    secure_directory_permissions "$data_dir"
    secure_file_permissions "$data_dir"
    set_ownership "$data_dir"

    if [[ "$PLATFORM" == "windows" ]]; then
        windows_specific_hardening "$data_dir"
    fi

    if validate_permissions "$data_dir"; then
        log "INFO" "✓ File permission hardening completed successfully"
        echo
        echo -e "${GREEN}Security hardening completed!${NC}"
        echo "Data directory: $data_dir"
        echo "All sensitive files are now secured with appropriate permissions."
    else
        log "WARNING" "Permission hardening completed with warnings"
        echo
        echo -e "${YELLOW}Security hardening completed with warnings.${NC}"
        echo "Check the output above for permission issues."
        exit 1
    fi
}

# Run with error handling
trap 'log "ERROR" "Permission hardening failed"' ERR

main "$@"