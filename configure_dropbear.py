import sys,time, subprocess
from utils import helpers
from managers import config_manager, service_manager

def configure_new_dropbear_port():
    DROPBEAR_PORTS = ["10003","12003", "13003", "14003", "15003"]

    try:
        configs = helpers.Helpers.load_app_config()
        dropbear_config_path = configs['dropbear_config']

        configManager = config_manager.ConfigManager(dropbear_config_path, configs['backup_dir'])
        dropbear_config = configManager.load(dropbear_config_path, is_json=False)
        current_port = extract_dropbear_port(dropbear_config.split('\n'))

        new_port = None
        if not helpers.Helpers.is_port_listening(current_port):
            for dropbear_port in DROPBEAR_PORTS:
                if not helpers.Helpers.is_port_listening(dropbear_port):
                    new_port = dropbear_port
                    break
        else:
            print("The current dropbear port is not in use, port is not the reason for the Dropbear fail")
            sys.exit(1)
        
        if not new_port:
            print("Failed to configure new port for Dropbear")
            sys.exit(1)

        new_config = set_new_dropbear_port(dropbear_config.split('\n'), new_port)
        change_dropbear_config(configManager, new_config, dropbear_config_path)

        time.sleep(5)

        subprocess.run(
            ["systemctl", "status", "dropbear"],
            text=True,
            capture_output=True
        )

        time.sleep(3)
        
        # result = serviceManager.status('dropbear')
        # if result.returncode == 0:
        #     print(f"Dropbear is configured properly and working")
        #     modify_dropbear_port_in_configs(new_port)
        #     sys.exit(0)
        
        # else:
        #     print("Failed to configure SSH Dropbear, reversing the old config")
        #     change_dropbear_config(configManager, dropbear_config, dropbear_config_path)
        #     serviceManager.restart('dropbear')
        #     sys.exit(1)


    except Exception as e:
        print(e)
        sys.exit(1)

def modify_dropbear_port_in_configs(port):
    configs = helpers.Helpers.load_app_config()
    configs['dropbear_port'] = port 
    
    helpers.Helpers.modify_app_config(configs)

def extract_dropbear_port( lines: list ):
    for line in lines:
        if line.startswith("#DROPBEAR_PORT="):
            return line.split('=',1)[1].strip()
        
    print("Dropbear config does not contain dropbear port")
    sys.exit(1)

def set_new_dropbear_port( lines: list, port:str ):
    new_config = ""
    for line in lines:
        if line.startswith("#DROPBEAR_PORT="):
            new_config += f"DROPBEAR_PORT={port}\n"
        elif 'DROPBEAR_EXTRA_ARGS="-b /etc/issue.net"' in line:
            new_config += 'DROPBEAR_EXTRA_ARGS="-b /etc/issue.net"\n'
        else:
            new_config += f"{line}\n"     
    
    return new_config.strip()

def change_dropbear_config(configManager: config_manager.ConfigManager, config:str, config_path:str):
    configManager.save(config, config_path, create_backup=False, is_json=False)

if __name__  == "__main__":
    configure_new_dropbear_port()
