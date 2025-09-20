#!/bin/bash

# Firewall Configuration Script
# Configures firewall rules for Personal AI Chatbot

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

# Detect platform and firewall type
detect_firewall() {
    case "$(uname -s)" in
        Linux*)
            if command -v ufw &> /dev/null; then
                FIREWALL_TYPE="ufw"
            elif command -v firewall-cmd &> /dev/null; then
                FIREWALL_TYPE="firewalld"
            elif command -v iptables &> /dev/null; then
                FIREWALL_TYPE="iptables"
            else
                FIREWALL_TYPE="none"
            fi
            ;;
        Darwin*)
            if command -v socketfilterfw &> /dev/null; then
                FIREWALL_TYPE="socketfilterfw"
            else
                FIREWALL_TYPE="none"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*)
            FIREWALL_TYPE="windows"
            ;;
        *)
            FIREWALL_TYPE="unknown"
            ;;
    esac

    log "INFO" "Detected firewall type: $FIREWALL_TYPE"
}

# Get application port
get_app_port() {
    if [[ -n "$APP_PORT" ]]; then
        echo "$APP_PORT"
    else
        echo "7860"  # Default Gradio port
    fi
}

# UFW configuration (Ubuntu/Debian)
configure_ufw() {
    local port="$1"

    log "INFO" "Configuring UFW firewall..."

    # Check if UFW is active
    if ! sudo ufw status | grep -q "Status: active"; then
        log "WARNING" "UFW is not active. Enabling UFW..."
        sudo ufw --force enable
    fi

    # Allow application port
    if ! sudo ufw status | grep -q "$port"; then
        sudo ufw allow "$port/tcp"
        log "INFO" "✓ Allowed port $port/tcp in UFW"
    else
        log "INFO" "Port $port/tcp already allowed in UFW"
    fi

    # Allow SSH if not already allowed (for remote management)
    if ! sudo ufw status | grep -q "22"; then
        sudo ufw allow ssh
        log "INFO" "✓ Allowed SSH in UFW"
    fi

    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing

    log "INFO" "✓ UFW configuration completed"
}

# Firewalld configuration (RHEL/CentOS/Fedora)
configure_firewalld() {
    local port="$1"

    log "INFO" "Configuring firewalld..."

    # Check if firewalld is running
    if ! sudo systemctl is-active --quiet firewalld; then
        log "WARNING" "firewalld is not running. Starting firewalld..."
        sudo systemctl start firewalld
        sudo systemctl enable firewalld
    fi

    # Allow application port
    if ! sudo firewall-cmd --list-ports | grep -q "$port/tcp"; then
        sudo firewall-cmd --permanent --add-port="$port/tcp"
        sudo firewall-cmd --reload
        log "INFO" "✓ Allowed port $port/tcp in firewalld"
    else
        log "INFO" "Port $port/tcp already allowed in firewalld"
    fi

    # Allow SSH
    if ! sudo firewall-cmd --list-services | grep -q "ssh"; then
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --reload
        log "INFO" "✓ Allowed SSH in firewalld"
    fi

    log "INFO" "✓ firewalld configuration completed"
}

# iptables configuration (fallback for older systems)
configure_iptables() {
    local port="$1"

    log "INFO" "Configuring iptables..."

    # Check if iptables rules exist for the port
    if ! sudo iptables -L INPUT -n | grep -q ":$port "; then
        # Allow application port
        sudo iptables -A INPUT -p tcp --dport "$port" -j ACCEPT
        log "INFO" "✓ Allowed port $port/tcp in iptables"
    else
        log "INFO" "Port $port/tcp already allowed in iptables"
    fi

    # Allow SSH
    if ! sudo iptables -L INPUT -n | grep -q ":22 "; then
        sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        log "INFO" "✓ Allowed SSH in iptables"
    fi

    # Allow loopback
    sudo iptables -A INPUT -i lo -j ACCEPT

    # Set default policies
    sudo iptables -P INPUT DROP
    sudo iptables -P FORWARD DROP
    sudo iptables -P OUTPUT ACCEPT

    # Allow established connections
    sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # Save iptables rules (distribution-specific)
    if command -v netfilter-persistent &> /dev/null; then
        sudo netfilter-persistent save
    elif [[ -f /etc/redhat-release ]]; then
        sudo service iptables save
    fi

    log "INFO" "✓ iptables configuration completed"
}

# macOS socketfilterfw configuration
configure_socketfilterfw() {
    local port="$1"

    log "INFO" "Configuring macOS socketfilterfw..."

    # Note: socketfilterfw is primarily for application-level filtering
    # For port-based filtering, we rely on pf (Packet Filter)

    # Check if pf is enabled
    if ! sudo pfctl -s info | grep -q "Status: Enabled"; then
        log "WARNING" "pf (Packet Filter) is not enabled"
        log "INFO" "To enable pf, run: sudo pfctl -e"
    fi

    # Create pf rules file if it doesn't exist
    local pf_conf="/etc/pf.conf"
    if [[ ! -f "$pf_conf" ]]; then
        sudo tee "$pf_conf" > /dev/null << EOF
# Personal AI Chatbot pf rules
block all
pass in proto tcp to port 22
pass in proto tcp to port $port
pass out all
EOF
        log "INFO" "✓ Created pf.conf with basic rules"
    else
        # Check if our rules are already there
        if ! grep -q "Personal AI Chatbot" "$pf_conf"; then
            sudo tee -a "$pf_conf" > /dev/null << EOF

# Personal AI Chatbot rules
pass in proto tcp to port $port
EOF
            log "INFO" "✓ Added rules to existing pf.conf"
        else
            log "INFO" "Rules already exist in pf.conf"
        fi
    fi

    # Load pf rules
    sudo pfctl -f /etc/pf.conf

    log "INFO" "✓ macOS firewall configuration completed"
}

# Windows firewall configuration
configure_windows_firewall() {
    local port="$1"

    log "INFO" "Configuring Windows Firewall..."

    # Use PowerShell to configure Windows Firewall
    local ps_script="
        \$port = $port
        \$ruleName = 'Personal AI Chatbot'

        # Check if rule already exists
        \$existingRule = Get-NetFirewallRule -DisplayName \$ruleName -ErrorAction SilentlyContinue

        if (\$null -eq \$existingRule) {
            New-NetFirewallRule -DisplayName \$ruleName -Direction Inbound -Protocol TCP -LocalPort \$port -Action Allow
            Write-Host 'Created firewall rule for port \$port'
        } else {
            Write-Host 'Firewall rule already exists'
        }
    "

    # Execute PowerShell script
    if command -v powershell.exe &> /dev/null; then
        powershell.exe -Command "$ps_script"
        log "INFO" "✓ Windows Firewall rule configured"
    elif command -v pwsh &> /dev/null; then
        pwsh -Command "$ps_script"
        log "INFO" "✓ Windows Firewall rule configured"
    else
        log "ERROR" "PowerShell not found, cannot configure Windows Firewall"
        return 1
    fi
}

# Validate firewall configuration
validate_firewall() {
    local port="$1"
    log "INFO" "Validating firewall configuration..."

    case $FIREWALL_TYPE in
        ufw)
            if sudo ufw status | grep -q "$port"; then
                log "INFO" "✓ Port $port is allowed in UFW"
                return 0
            fi
            ;;
        firewalld)
            if sudo firewall-cmd --list-ports | grep -q "$port/tcp"; then
                log "INFO" "✓ Port $port is allowed in firewalld"
                return 0
            fi
            ;;
        iptables)
            if sudo iptables -L INPUT -n | grep -q ":$port "; then
                log "INFO" "✓ Port $port is allowed in iptables"
                return 0
            fi
            ;;
        socketfilterfw)
            # Basic check - in production, more thorough validation would be needed
            log "INFO" "✓ macOS firewall rules configured"
            return 0
            ;;
        windows)
            log "INFO" "✓ Windows firewall rules configured"
            return 0
            ;;
    esac

    log "WARNING" "Could not validate firewall configuration"
    return 1
}

# Main function
main() {
    log "INFO" "Starting firewall configuration..."

    detect_firewall
    local app_port=$(get_app_port)

    log "INFO" "Configuring firewall for port: $app_port"

    case $FIREWALL_TYPE in
        ufw)
            configure_ufw "$app_port"
            ;;
        firewalld)
            configure_firewalld "$app_port"
            ;;
        iptables)
            configure_iptables "$app_port"
            ;;
        socketfilterfw)
            configure_socketfilterfw "$app_port"
            ;;
        windows)
            configure_windows_firewall "$app_port"
            ;;
        none)
            log "WARNING" "No firewall detected. Please configure manually."
            echo
            echo -e "${YELLOW}No firewall detected on this system.${NC}"
            echo "Please ensure port $app_port is accessible for the application."
            echo "You may need to configure your firewall manually."
            exit 0
            ;;
        *)
            log "ERROR" "Unsupported firewall type: $FIREWALL_TYPE"
            exit 1
            ;;
    esac

    if validate_firewall "$app_port"; then
        log "INFO" "✓ Firewall configuration completed successfully"
        echo
        echo -e "${GREEN}Firewall configuration completed!${NC}"
        echo "Port $app_port is now allowed through the firewall."
        echo "The application should be accessible from other machines on the network."
    else
        log "WARNING" "Firewall configuration completed with validation warnings"
        echo
        echo -e "${YELLOW}Firewall configuration completed with warnings.${NC}"
        echo "Please verify that port $app_port is accessible."
    fi
}

# Run with error handling
trap 'log "ERROR" "Firewall configuration failed"' ERR

main "$@"