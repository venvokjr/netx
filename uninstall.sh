#!/bin/bash

set -e

echo "=========================================="
echo "        NET-X Uninstaller"
echo "=========================================="

echo "[1/10] Stopping services..."

systemctl stop ws_proxy.service 2>/dev/null || true
systemctl disable ws_proxy.service 2>/dev/null || true

systemctl stop xray 2>/dev/null || true
systemctl disable xray 2>/dev/null || true

systemctl stop nginx 2>/dev/null || true

echo "[2/10] Removing ws_proxy service..."

rm -f /etc/systemd/system/ws_proxy.service
systemctl daemon-reload

echo "[3/10] Purging Xray..."

apt purge -y xray || true
apt autoremove -y

rm -rf /usr/local/etc/xray
rm -f /usr/local/bin/xray
rm -rf /var/log/xray

echo "[4/10] Purging Dropbear..."

systemctl stop dropbear 2>/dev/null || true
apt purge -y dropbear || true
apt autoremove -y

rm -rf /etc/dropbear

echo "[5/10] Removing Nginx configuration..."

rm -f /etc/nginx/sites-enabled/netx
rm -f /etc/nginx/sites-available/netx

nginx -t && systemctl reload nginx || true

echo "[6/10] Removing NET-X executable..."

rm -f /usr/local/bin/netx

echo "[7/10] Removing NET-X configuration..."

rm -rf /opt/netx/configs

echo "[8/10] Removing NET-X files..."

rm -rf /opt/netx

echo "[9/10] Cleaning temporary files..."

rm -f /tmp/xray_config.json
rm -f /tmp/netx_*

echo "[10/10] Finished."

echo
echo "=========================================="
echo "NET-X has been removed."
echo
echo "NOT removed:"
echo "  ✓ Certbot"
echo "  ✓ Let's Encrypt certificates"
echo "  ✓ /etc/letsencrypt"
echo "=========================================="