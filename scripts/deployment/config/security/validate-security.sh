#!/bin/bash

# Security Validation Script
# Validates security configuration for Personal AI Chatbot

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

# Global variables
ISSUES_FOUND=0
WARNINGS_FOUND=0

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

# Check file permissions
check_file_permissions() {
    local data_dir="$1"
    log "INFO" "Checking file permissions..."

    # Check main data directory
    if [[ -d "$data_dir" ]]; then
        local perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%Lp" "$data_dir" 2>/dev/null)
        if [[ "$perms" != "700" ]]; then
            log "ERROR" "Data directory permissions should be 700, got $perms"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        else
            log "INFO" "✓ Data directory permissions are secure"
        fi
    else
        log "WARNING" "Data directory does not exist: $data_dir"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
    fi

    # Check config files
    local config_files=(
        "$data_dir/config/app_config.json"
        "$data_dir/.env"
    )

    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            local perms=$(stat -c "%a" "$config_file" 2>/dev/null || stat -f "%Lp" "$config_file" 2>/dev/null)
            if [[ "$perms" != "600" ]]; then
                log "ERROR" "Config file permissions should be 600, got $perms for $config_file"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            else
                log "INFO" "✓ Config file permissions are secure: $config_file"
            fi
        fi
    done
}

# Check environment variables
check_environment_variables() {
    log "INFO" "Checking environment variables..."

    # Required variables
    local required_vars=("OPENROUTER_API_KEY" "SECRET_KEY" "ENCRYPTION_KEY")

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log "ERROR" "Required environment variable '$var' is not set"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        else
            log "INFO" "✓ Required variable '$var' is set"
        fi
    done

    # Check API key format
    if [[ -n "$OPENROUTER_API_KEY" ]]; then
        if [[ ! "$OPENROUTER_API_KEY" =~ ^sk-or-v1- ]]; then
            log "ERROR" "OPENROUTER_API_KEY does not have valid format (should start with 'sk-or-v1-')"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    fi

    # Check key lengths
    if [[ -n "$SECRET_KEY" && ${#SECRET_KEY} -lt 32 ]]; then
        log "WARNING" "SECRET_KEY is shorter than recommended (32+ characters)"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
    fi

    if [[ -n "$ENCRYPTION_KEY" && ${#ENCRYPTION_KEY} -lt 32 ]]; then
        log "WARNING" "ENCRYPTION_KEY is shorter than recommended (32+ characters)"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
    fi
}

# Check network security
check_network_security() {
    log "INFO" "Checking network security..."

    # Get application port
    local app_port=${APP_PORT:-7860}

    # Check if port is accessible from outside
    case $PLATFORM in
        linux)
            # Check if port is listening
            if command -v ss &> /dev/null; then
                if ss -tln | grep -q ":$app_port "; then
                    log "INFO" "✓ Application port $app_port is listening"
                else
                    log "WARNING" "Application port $app_port is not listening"
                    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
                fi
            fi

            # Check firewall status
            if command -v ufw &> /dev/null; then
                if sudo ufw status | grep -q "$app_port"; then
                    log "INFO" "✓ Port $app_port is allowed in UFW"
                else
                    log "WARNING" "Port $app_port may not be allowed in firewall"
                    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
                fi
            fi
            ;;
        macos)
            # Check if port is listening
            if netstat -an | grep -q "LISTEN.*:$app_port"; then
                log "INFO" "✓ Application port $app_port is listening"
            else
                log "WARNING" "Application port $app_port is not listening"
                WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
            fi
            ;;
    esac
}

# Check SSL/TLS configuration
check_ssl_configuration() {
    log "INFO" "Checking SSL/TLS configuration..."

    # Check if HTTPS is configured
    if [[ "${APP_PORT:-7860}" == "443" ]] || [[ "${APP_PORT:-7860}" == "8443" ]]; then
        log "INFO" "✓ Application appears to be configured for HTTPS"
    else
        log "WARNING" "Application is not configured for HTTPS (port ${APP_PORT:-7860})"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
    fi

    # Check for SSL certificates
    local cert_files=("/etc/ssl/certs/" "/etc/pki/tls/certs/")
    local cert_found=false

    for cert_dir in "${cert_files[@]}"; do
        if [[ -d "$cert_dir" ]] && [[ $(find "$cert_dir" -name "*.pem" -o -name "*.crt" 2>/dev/null | wc -l) -gt 0 ]]; then
            cert_found=true
            break
        fi
    done

    if [[ "$cert_found" == true ]]; then
        log "INFO" "✓ SSL certificates are available"
    else
        log "INFO" "No SSL certificates found (may be using self-signed or Let's Encrypt)"
    fi
}

# Check for security vulnerabilities
check_security_vulnerabilities() {
    log "INFO" "Checking for common security vulnerabilities..."

    # Check if running as root
    if [[ "$EUID" -eq 0 ]]; then
        log "WARNING" "Application is running as root - this is not recommended"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
    else
        log "INFO" "✓ Application is not running as root"
    fi

    # Check for world-writable files
    local data_dir="$1"
    if [[ -d "$data_dir" ]]; then
        local world_writable=$(find "$data_dir" -type f -perm -002 2>/dev/null | wc -l)
        if [[ $world_writable -gt 0 ]]; then
            log "ERROR" "Found $world_writable world-writable files in data directory"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        else
            log "INFO" "✓ No world-writable files found"
        fi
    fi

    # Check for insecure umask
    local current_umask=$(umask)
    if [[ "$current_umask" != "0022" && "$current_umask" != "0077" ]]; then
        log "WARNING" "Current umask ($current_umask) may allow overly permissive file creation"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
    fi
}

# Check dependencies for known vulnerabilities
check_dependencies() {
    log "INFO" "Checking dependencies for security issues..."

    # Check if safety is available
    if command -v safety &> /dev/null; then
        log "INFO" "Running safety check on dependencies..."

        # Try to find requirements.txt
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        local project_root="$(cd "$script_dir/../../../../.." && pwd)"
        local requirements_file="$project_root/requirements.txt"

        if [[ -f "$requirements_file" ]]; then
            if safety check --file "$requirements_file" 2>/dev/null; then
                log "INFO" "✓ No known vulnerabilities found in dependencies"
            else
                log "WARNING" "Potential vulnerabilities found in dependencies"
                WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
            fi
        else
            log "WARNING" "requirements.txt not found, skipping dependency check"
        fi
    else
        log "INFO" "Safety tool not available, skipping dependency vulnerability check"
        log "INFO" "Install safety with: pip install safety"
    fi
}

# Generate security report
generate_security_report() {
    log "INFO" "Generating security validation report..."

    echo
    echo "========================================"
    echo "  Personal AI Chatbot Security Report   "
    echo "========================================"
    echo
    echo "Platform: $PLATFORM"
    echo "Data Directory: $1"
    echo "Timestamp: $(date)"
    echo
    echo "Security Issues Found: $ISSUES_FOUND"
    echo "Security Warnings: $WARNINGS_FOUND"
    echo

    if [[ $ISSUES_FOUND -eq 0 && $WARNINGS_FOUND -eq 0 ]]; then
        echo -e "${GREEN}✓ SECURITY STATUS: SECURE${NC}"
        echo "All security checks passed successfully."
    elif [[ $ISSUES_FOUND -eq 0 ]]; then
        echo -e "${YELLOW}⚠ SECURITY STATUS: WARNINGS${NC}"
        echo "Security checks passed with warnings."
    else
        echo -e "${RED}✗ SECURITY STATUS: ISSUES FOUND${NC}"
        echo "Security issues require immediate attention."
    fi

    echo
    echo "Recommendations:"
    if [[ $ISSUES_FOUND -gt 0 ]]; then
        echo "• Address all security issues before deploying to production"
        echo "• Review file permissions and environment variables"
    fi
    if [[ $WARNINGS_FOUND -gt 0 ]]; then
        echo "• Consider addressing security warnings for better protection"
    fi
    echo "• Regularly run this validation script"
    echo "• Keep dependencies updated and monitor for vulnerabilities"
    echo
}

# Main function
main() {
    log "INFO" "Starting security validation..."

    detect_platform
    local data_dir=$(get_data_dir)

    log "INFO" "Using data directory: $data_dir"

    check_file_permissions "$data_dir"
    check_environment_variables
    check_network_security
    check_ssl_configuration
    check_security_vulnerabilities "$data_dir"
    check_dependencies

    generate_security_report "$data_dir"

    # Exit with appropriate code
    if [[ $ISSUES_FOUND -gt 0 ]]; then
        log "ERROR" "Security validation failed with $ISSUES_FOUND issues"
        exit 1
    elif [[ $WARNINGS_FOUND -gt 0 ]]; then
        log "WARNING" "Security validation completed with $WARNINGS_FOUND warnings"
        exit 2
    else
        log "INFO" "✓ Security validation completed successfully"
        exit 0
    fi
}

# Run with error handling
trap 'log "ERROR" "Security validation failed with error"' ERR

main "$@"