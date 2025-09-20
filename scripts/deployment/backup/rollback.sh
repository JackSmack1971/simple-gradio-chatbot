#!/bin/bash

# Rollback Script for Personal AI Chatbot
# Rolls back application to previous version or configuration state

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

# Get installation directory
get_install_dir() {
    if [[ -n "$INSTALL_DIR" ]]; then
        echo "$INSTALL_DIR"
    elif [[ "$PLATFORM" == "linux" ]]; then
        echo "/opt/personal-ai-chatbot"
    elif [[ "$PLATFORM" == "macos" ]]; then
        echo "/Applications/PersonalAIChatbot"
    elif [[ "$PLATFORM" == "windows" ]]; then
        echo "$ProgramFiles/PersonalAIChatbot"
    else
        echo "."
    fi
}

# Stop application
stop_application() {
    log "INFO" "Stopping application..."

    # Find and stop Python processes
    local pids=$(pgrep -f "python.*main.py" || true)

    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 5

        # Force kill if still running
        local remaining_pids=$(pgrep -f "python.*main.py" || true)
        if [[ -n "$remaining_pids" ]]; then
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
            log "INFO" "✓ Application forcefully stopped"
        else
            log "INFO" "✓ Application stopped gracefully"
        fi
    else
        log "INFO" "Application not running"
    fi

    # Stop systemd service if applicable
    if command -v systemctl &> /dev/null && systemctl is-active --quiet personal-ai-chatbot 2>/dev/null; then
        sudo systemctl stop personal-ai-chatbot
        log "INFO" "✓ systemd service stopped"
    fi
}

# Create rollback point
create_rollback_point() {
    local install_dir="$1"
    local data_dir="$2"

    log "INFO" "Creating rollback point..."

    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local rollback_dir="$data_dir/rollback/$timestamp"

    mkdir -p "$rollback_dir"

    # Backup current application files
    if [[ -d "$install_dir" ]]; then
        cp -r "$install_dir" "$rollback_dir/app_backup"
        log "INFO" "✓ Application files backed up"
    fi

    # Backup current data
    if [[ -d "$data_dir" ]]; then
        mkdir -p "$rollback_dir/data_backup"
        cp -r "$data_dir/config" "$rollback_dir/data_backup/" 2>/dev/null || true
        cp -r "$data_dir/conversations" "$rollback_dir/data_backup/" 2>/dev/null || true
        cp "$data_dir/.env" "$rollback_dir/data_backup/" 2>/dev/null || true
        log "INFO" "✓ Data files backed up"
    fi

    # Create rollback manifest
    cat > "$rollback_dir/rollback-manifest.txt" << EOF
Personal AI Chatbot Rollback Point
Created: $(date)
Install Directory: $install_dir
Data Directory: $data_dir
Timestamp: $timestamp

This rollback point contains:
- Application files from: $install_dir
- Configuration and data from: $data_dir

To rollback to this point, run:
./scripts/deployment/backup/rollback.sh --rollback-point $timestamp
EOF

    log "INFO" "✓ Rollback point created: $rollback_dir"
    echo "$rollback_dir"
}

# List available rollback points
list_rollback_points() {
    local data_dir="$1"
    local rollback_dir="$data_dir/rollback"

    if [[ ! -d "$rollback_dir" ]]; then
        log "INFO" "No rollback points found"
        return 1
    fi

    echo "Available rollback points:"
    echo

    local count=1
    for point_dir in $(find "$rollback_dir" -mindepth 1 -maxdepth 1 -type d | sort -r); do
        local point_name=$(basename "$point_dir")
        local manifest="$point_dir/rollback-manifest.txt"

        if [[ -f "$manifest" ]]; then
            echo "$count) $point_name"
            echo "   Created: $(grep "Created:" "$manifest" | cut -d: -f2- | xargs)"
            echo "   Path: $point_dir"
            echo
            ((count++))
        fi
    done
}

# Select rollback point
select_rollback_point() {
    local data_dir="$1"
    local rollback_dir="$data_dir/rollback"

    list_rollback_points "$data_dir"

    local points=($(find "$rollback_dir" -mindepth 1 -maxdepth 1 -type d | sort -r))

    if [[ ${#points[@]} -eq 0 ]]; then
        log "ERROR" "No rollback points available"
        exit 1
    fi

    echo -n "Enter rollback point number (1-${#points[@]}): "
    read -r selection

    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [[ $selection -lt 1 ]] || [[ $selection -gt ${#points[@]} ]]; then
        log "ERROR" "Invalid selection: $selection"
        exit 1
    fi

    local selected_index=$((selection - 1))
    echo "${points[$selected_index]}"
}

# Perform rollback
perform_rollback() {
    local rollback_point="$1"
    local install_dir="$2"
    local data_dir="$3"
    local dry_run="${4:-false}"

    log "INFO" "Performing rollback to: $(basename "$rollback_point")"

    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "DRY RUN - No changes will be made"
    fi

    # Check rollback point integrity
    local manifest="$rollback_point/rollback-manifest.txt"
    if [[ ! -f "$manifest" ]]; then
        log "ERROR" "Invalid rollback point: manifest not found"
        exit 1
    fi

    log "INFO" "✓ Rollback point validated"

    # Stop application
    stop_application

    # Rollback application files
    local app_backup="$rollback_point/app_backup"
    if [[ -d "$app_backup" ]]; then
        if [[ "$dry_run" == "true" ]]; then
            log "INFO" "[DRY RUN] Would restore application files from: $app_backup"
            find "$app_backup" -type f | wc -l | xargs printf "[DRY RUN] %d application files\n"
        else
            # Backup current state before rollback
            local current_backup="$install_dir.backup.$(date '+%Y%m%d_%H%M%S')"
            if [[ -d "$install_dir" ]]; then
                mv "$install_dir" "$current_backup"
                log "INFO" "✓ Current application backed up to: $current_backup"
            fi

            cp -r "$app_backup" "$install_dir"
            log "INFO" "✓ Application files rolled back"
        fi
    else
        log "WARNING" "No application backup found in rollback point"
    fi

    # Rollback data files
    local data_backup="$rollback_point/data_backup"
    if [[ -d "$data_backup" ]]; then
        if [[ "$dry_run" == "true" ]]; then
            log "INFO" "[DRY RUN] Would restore data files from: $data_backup"
            find "$data_backup" -type f | wc -l | xargs printf "[DRY RUN] %d data files\n"
        else
            # Restore configuration
            if [[ -d "$data_backup/config" ]]; then
                cp -r "$data_backup/config" "$data_dir/"
                log "INFO" "✓ Configuration files rolled back"
            fi

            # Restore conversations (optional - may be large)
            if [[ -d "$data_backup/conversations" ]]; then
                cp -r "$data_backup/conversations" "$data_dir/"
                log "INFO" "✓ Conversation data rolled back"
            fi

            # Restore environment file
            if [[ -f "$data_backup/.env" ]]; then
                cp "$data_backup/.env" "$data_dir/"
                log "INFO" "✓ Environment file rolled back"
            fi
        fi
    else
        log "WARNING" "No data backup found in rollback point"
    fi

    # Restore permissions
    if [[ "$dry_run" != "true" ]]; then
        log "INFO" "Restoring file permissions..."
        ./scripts/deployment/config/security/harden-permissions.sh
    fi

    log "INFO" "Rollback completed successfully!"
}

# Main rollback function
main() {
    # Parse command line arguments
    ROLLBACK_POINT=""
    DRY_RUN=false
    CREATE_POINT=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --rollback-point)
                ROLLBACK_POINT="$2"
                shift 2
                ;;
            --create-point)
                CREATE_POINT=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --list)
                LIST_ONLY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--rollback-point POINT] [--create-point] [--dry-run] [--list]"
                echo "  --rollback-point POINT: Specify rollback point to restore"
                echo "  --create-point: Create a new rollback point"
                echo "  --dry-run: Show what would be rolled back without making changes"
                echo "  --list: List available rollback points"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    detect_platform
    local install_dir=$(get_install_dir)
    local data_dir=$(get_data_dir)

    log "INFO" "Starting rollback operations..."
    log "INFO" "Install Directory: $install_dir"
    log "INFO" "Data Directory: $data_dir"

    # Handle different operations
    if [[ "$LIST_ONLY" == "true" ]]; then
        list_rollback_points "$data_dir"
        exit 0
    fi

    if [[ "$CREATE_POINT" == "true" ]]; then
        create_rollback_point "$install_dir" "$data_dir"
        exit 0
    fi

    # Perform rollback
    if [[ -z "$ROLLBACK_POINT" ]]; then
        # Interactive selection
        ROLLBACK_POINT=$(select_rollback_point "$data_dir")
    fi

    if [[ ! -d "$ROLLBACK_POINT" ]]; then
        log "ERROR" "Rollback point not found: $ROLLBACK_POINT"
        exit 1
    fi

    # Confirm rollback
    if [[ "$DRY_RUN" != "true" ]]; then
        echo
        echo -e "${YELLOW}WARNING: This will rollback the application to a previous state!${NC}"
        echo "Rollback Point: $(basename "$ROLLBACK_POINT")"
        echo "Install Directory: $install_dir"
        echo "Data Directory: $data_dir"
        echo
        echo -n "Continue with rollback? (y/N): "
        read -r confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log "INFO" "Rollback cancelled by user"
            exit 0
        fi
    fi

    # Perform the rollback
    perform_rollback "$ROLLBACK_POINT" "$install_dir" "$data_dir" "$DRY_RUN"

    # Post-rollback actions
    if [[ "$DRY_RUN" != "true" ]]; then
        echo
        echo -e "${GREEN}Rollback completed!${NC}"
        echo
        echo "Next steps:"
        echo "1. Review rolled back files"
        echo "2. Run validation checks:"
        echo "   python scripts/deployment/validation/validate-config.py"
        echo "   python scripts/deployment/validation/health-check.py"
        echo "3. Restart the application:"
        echo "   ./run.sh"
        echo
        echo "If issues occur, you can find backups in:"
        echo "  $install_dir.backup.*"
        echo "  $data_dir/rollback/"
    fi
}

# Run with error handling
trap 'log "ERROR" "Rollback failed"' ERR

main "$@"