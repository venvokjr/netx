import sys
from managers import service_manager

CONFIGURATION = """
[Unit]
Description=WebSocket Proxy for SSH Dropbear
After=network.target dropbear.service

[Service]
Type=simple
WorkingDirectory=/opt/netx
ExecStart=/usr/bin/python3 /opt/netx/ws_proxy.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

def configure_ws_proxy_daemon():
    try:
        create_service_file()
        service = service_manager.ServiceManager()
        service.start('ws_proxy')
        service.enable('ws_proxy')
        service.daemon_reload()

        result = service.status('ws_proxy')
        if result.returncode != 0:
            print('Failed to start Websocket Proxy')
            sys.exit(1)
        
        print('Websocket Proxy started successfully')
        sys.exit(0) 
    
    except Exception as e:
        print(e)
        sys.exit(1)

def create_service_file():
    with open('/etc/systemd/system/ws_proxy.service', 'w') as f:
        f.write(CONFIGURATION.strip())

if __name__ == '__main__':
    create_service_file()