import sys
from utils import helpers
from managers import config_manager

def configure_nginx_config():
    try:

        configs = helpers.Helpers.load_app_config()
        nginx_config_path = configs['nginx_config']
        configManager = config_manager.ConfigManager(nginx_config_path, configs['backup_dir'])

        nginx_conf = str(configManager.load(is_json=False))

        new_config = replace_variables(nginx_conf,configs)

        configManager.save(new_config, create_backup=False, is_json=False)
        sys.exit(0)
        
    except Exception as e:
        print(e)
        sys.exit(1)
    

def replace_variables(nginx_conf:str, configs:dict):
    domain_replaced = nginx_conf.replace("__DOMAIN__",f"{configs['domain']}", -1)
    vmess_path_replaced = domain_replaced.replace("__VMESS_PATH__",f"{configs['vmess_path']}", -1)
    vless_path_replaced = vmess_path_replaced.replace("__VLESS_PATH__",f"{configs['vless_path']}", -1)
    vmess_port_replaced = vless_path_replaced.replace("__VMESS_PORT__",f"{configs['vmess_port']}", -1)
    vless_port_replaced = vmess_port_replaced.replace("__VLESS_PORT__",f"{configs['vless_port']}", -1)
    wsproxy_port_replaced =     vless_port_replaced.replace("__WS_PROXY_PORT__",f"{configs['wsproxy_port']}", -1)

    return wsproxy_port_replaced


if __name__ == "__main__":
    configure_nginx_config()

