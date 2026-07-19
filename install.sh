#!/bin/bash

VLESS_PORT=10000
VMESS_PORT=10001
VLESS_PATH="/vless"
VMESS_PATH="/vmess"

info(){
    echo -e "\e[1;34m[*] $1\e[0m"
}

success(){
    echo -e "\e[1;32m[✓] $1\e[0m"
}

error(){
    echo -e "\e[1;31m[x] $1\e[0m"
}

check_root(){
    info "Checking the user status"
    if [[ $EUID != 0 ]]; then
        error "Please run as a root"
        exit 1
    fi
    success "Running as a root user"
}

check_os(){
    info "Checking the OS Info"

    . /etc/os-release 
    os_id=$ID
    version_id=$VERSION_ID

    if [[ "${os_id,,}" != 'ubuntu' ]]; then
        error "You must run the installer inside an Ubuntu distro"
        exit 1
    fi

    if [[ "$version_id" != "24.04" && "$version_id" != "22.04" ]]; then
        error "You must run the installer inside Ubuntu v22.04 or v24.04"
        exit 1
    fi

    success "OS check passed successfully"
}

update_packages(){
    info "Updating package lists..."

    if ! apt update; then
        error "Failed to update package lists. Please check your internet connection."
        exit 1
    fi

    success "Package lists updated."
}

install_dependencies(){

    info "Installing dependencies..."
    if ! apt install -y curl wget unzip python3 python3-pip git python3-psutil nginx dnsutils certbot python3-certbot-nginx; then
        error "Failed to install dependencies..."
        exit 1
    fi

    success "Done Installing dependencies successfully..."       
}

install_xray(){
    info "Checking Xray Installation...."

    if command -v xray >/dev/null 2>&1; then
        success "Xray is already installed, skipping its installation.."

    else
        info "Xray not found, installing from github"

        if ! bash <(curl -Ls https://github.com/XTLS/Xray-install/raw/main/install-release.sh); then
            error "Failed to execute the Xray installer."
            exit 1
        fi

        if command -v xray >/dev/null 2>&1; then
            success "Xray installation successfully..."
        else
            error "Xray installation failed.."
            exit 1
        fi

    fi

}

install_dropbear(){
    info "Checking Dropbear installation"

    if command -v dropbear >/dev/null 2>&1; then
        success "Dropbear found, skipping its installation"
    
    else
        info "Dropbear not found, trying to install it"

        if ! sudo apt install -y dropbear; then
            error "Failed to install dropbear"
            exit 1
        fi

        if ! systemctl status is-active dropbear; then
            error "Dropbear is not active trying to configure by changing ports"
            
            chmod +x configure_dropbear.py
            if ! sudo python3 configure_dropbear.py; then
                error "Failed to configure dropbear"
                exit 1

            else
                success "Dropbear configuration is successfully"
            fi

        else
            success "Dropbear configured and installed  successfully"
        fi
    
    fi

}

install_netx_requirements() {
    if [[ -f /opt/netx/requirements.txt ]]; then
        info "Installing Python dependencies..."

        if ! python3 -m pip install --break-system-packages -r /opt/netx/requirements.txt; then
            error "Failed to install Python dependencies."
            exit 1
        fi

        success "Python dependencies installed."
    fi
}

install_netx(){

    URL="https://github.com/venvokjr/netx.git"

    info "Netx installation started"
    if ! command -v git >/dev/null 2>&1; then
        info "Git was not found, trying to install it"
        if ! apt install -y git; then
            error "Failed to install git"
            exit 1
        fi
    fi

    if [[ -d /opt/netx/ ]]; then

        info "Netx found, trying to update it"

        if ! cd /opt/netx; then 
            error "Failed to navigate to Netx directory"
            exit 1
        fi

        if ! git pull; then
            error "Failed to update netx using git"
            exit 1
        fi

        install_netx_requirements

        success "Netx was update using github"

    else
        info "Cloning and installing the netx using git"
        if ! git clone --depth 1 "$URL" /opt/netx; then
            error "Failed to download netx using git"
            exit 1
        fi

        install_netx_requirements

        success "Netx was downloaded successfully"
    fi

}

create_netx_executable() {

    info "Creating NET-X launcher..."

    cat > /usr/local/bin/netx << 'EOF'
#!/bin/bash
sudo python3 /opt/netx/main.py "$@"
EOF

    chmod +x /usr/local/bin/netx

    if [[ ! -x /usr/local/bin/netx ]]; then
        error "Failed to create NET-X launcher."
        exit 1
    fi

    success "NET-X launcher created successfully."
}

get_domain() {
    clear
    while true; do
        read -rp "Enter the domain/subdomain pointed to this VPS IP: " domain

        vps_domain=$(printf "%s" "$domain" | xargs)

        if [[ -z "$vps_domain" ]]; then
            error "Domain cannot be empty."
            continue
        fi

        if [[ ! "$vps_domain" =~ ^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$ ]]; then
            error "Invalid domain format."
            continue
        fi

        vps_ip=$(curl -4 -s https://api.ipify.org)

        if [[ -z "$vps_ip" ]]; then
            error "Unable to determine VPS public IP."
            exit 1
        fi

        if ! host -t A "$vps_domain" >/dev/null 2>&1; then
            error "Unable to resolve domain."
            continue
        fi

        domain_ip=$(host -t A "$vps_domain" | awk '/has address/ {print $NF}')

        if ! grep -qx "$vps_ip" <<< "$domain_ip"; then
            error "Domain does not point to this VPS."
            continue
        fi

        NETX_DOMAIN="$vps_domain"
        NETX_VPS_IP="$vps_ip"

        chmod +x set_config.py
        python3 set_config.py --domain $vps_domain

        success "Domain resolved successfully."
        break
    done
}

create_temp_nginx_config(){
    if ! cp /opt/netx/configs/nginx-temp.conf /etc/nginx/sites-available/netx; then
        error "Failed to copy the temporary nginx to sites available"
        exit 1
    fi

    if ! sed -i "s/__DOMAIN__/$NETX_DOMAIN/g" /etc/nginx/sites-available/netx; then
        error "Failed to configure Nginx domain."
        exit 1
    fi

    if ! ln -sf /etc/nginx/sites-available/netx \
             /etc/nginx/sites-enabled/netx; then
        error "Failed to enable Nginx site."
        exit 1
    fi
    
    if ! nginx -t; then
        error "Nginx configuration test failed."
        exit 1
    fi

    success "Temporary Nginx configuration created successfully."
}

reload_nginx() {
    info "Reloading Nginx..."

    if ! nginx -t >/dev/null 2>&1; then
        error "Nginx configuration test failed."
        exit 1
    fi

    systemctl reload nginx

    if [[ $? -ne 0 ]]; then
        error "Failed to reload Nginx."
        exit 1
    fi

    success "Nginx reloaded successfully."
}

install_certbot() {
    info "Installing Certbot..."

    if ! command -v certbot >/dev/null 2>&1; then
        error "Failed to install Certbot."
        exit 1
    fi

    success "Certbot installed successfully."
}

issue_certificate() {
    info "Requesting Let's Encrypt certificate..."

    certbot certonly \
        --nginx \
        --non-interactive \
        --agree-tos \
        --register-unsafely-without-email \
        -d "$NETX_DOMAIN"

    if [[ ! -f "/etc/letsencrypt/live/$NETX_DOMAIN/fullchain.pem" ]] || \
       [[ ! -f "/etc/letsencrypt/live/$NETX_DOMAIN/privkey.pem" ]]; then
        error "Certificate generation failed."
        exit 1
    fi

    success "Certificate issued successfully."
}

create_nginx_config() {
    info "Creating production Nginx configuration..."

    if ! cp /opt/netx/configs/nginx.conf /etc/nginx/sites-available/netx; then
        error "Failed to copy Nginx configuration."
        exit 1
    fi

    chmod +x configure_nginx.py
    if ! sudo python3 configure_nginx.py; then
        error "Failed to initialize nginx configuration"
        exit 1
    fi

    if ! ln -sf /etc/nginx/sites-available/netx \
        /etc/nginx/sites-enabled/netx; then
        error "Failed to enable Nginx site."
        exit 1
    fi

    if ! nginx -t; then
        error "Nginx configuration test failed."
        exit 1
    fi

    success "Production Nginx configuration created successfully."
}

create_xray_config() {
    info "Creating Xray configuration..."

    if ! cp /opt/netx/configs/config.json /tmp/netx-xray.json; then
        error "Failed to copy Xray configuration."
        exit 1
    fi

    # if ! replace_placeholders /tmp/netx-xray.json; then
    #     error "Failed to configure Xray."
    #     exit 1
    # fi

    if ! xray run -test -config /tmp/netx-xray.json; then
        error "Xray configuration validation failed."
        rm -f /tmp/netx-xray.json
        exit 1
    fi

    if ! mv /tmp/netx-xray.json /usr/local/etc/xray/config.json; then
        error "Failed to install Xray configuration."
        exit 1
    fi

    success "Xray configuration created successfully."
}

restart_xray() {
    info "Restarting Xray..."

    if ! systemctl restart xray; then
        error "Failed to restart Xray."
        exit 1
    fi

    if ! systemctl is-active --quiet xray; then
        error "Xray is not running."
        exit 1
    fi

    success "Xray restarted successfully."
}

configure_websocket_proxy(){
    info "Starting the webscokets proxy"
    chmod +x configure_ws_proxy.py
    if ! sudo configure_ws_proxy.py; then
        error "Failed to start websocket proxy"
        exit 1
    else
        success "Websocket proxy started successfully"
    fi
}

install_stunnel(){

    if ! sudo apt install -y stunnel4; then
        error 'Failed to install stunnel4'
        exit 1

    else
        chmod +x configure_stunnel.py
        if ! sudo python3 configure_stunnel.py; then
            error 'Failed to configure stunnel4'
            exit 1
        
        else
            success "Stunnel was installed and configured properly"
        fi

    fi
}

create_netx_config() {
    info "Creating NET-X configuration..."

    mkdir -p /etc/netx

    cat > /etc/netx/netx.conf << EOF
DOMAIN=$NETX_DOMAIN
PUBLI_IP=$NETX_VPS_IP

VLESS_PORT=$VLESS_PORT
VMESS_PORT=$VMESS_PORT

VLESS_PATH=$VLESS_PATH
VMESS_PATH=$VMESS_PATH
EOF

    success "NET-X configuration created."
}

finish() {
    clear
    echo
    echo "=========================================================="
    success "NET-X installation completed successfully!"
    echo "=========================================================="
    echo
    echo "Domain          : $NETX_DOMAIN"
    echo "HTTPS           : https://$NETX_DOMAIN"
    echo "Xray Config     : /usr/local/etc/xray/config.json"
    echo "Nginx Config    : /etc/nginx/sites-available/netx"
    echo "Certificate     : /etc/letsencrypt/live/$NETX_DOMAIN/"
    echo
    echo "Launch NET-X using:"
    echo "    netx"
    echo
}

main(){
    check_root
    check_os
    update_packages
    install_dependencies
    get_domain
    install_netx
    install_xray
    create_temp_nginx_config
    reload_nginx
    install_certbot
    issue_certificate
    install_dropbear
    install_stunnel
    configure_websocket_proxy
    create_xray_config
    create_nginx_config
    reload_nginx
    restart_xray
    create_netx_config
    create_netx_executable
    finish
}

main