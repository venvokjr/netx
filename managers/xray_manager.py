from managers.config_manager import ConfigManager
from managers.service_manager import ServiceManager
from models.xray_users import VlessUser,VmessUser,TrojanUser
import os

class XrayHelper:
    
    @staticmethod
    def add_client(config:dict, client:dict, protocol:str):
        inbounds = config.get("inbounds")

        if not inbounds:
            raise ValueError("Inbonds are not found")

        inbound_found = False
        for inbound in inbounds:
            if inbound.get('protocol') and inbound.get('protocol').lower() == protocol.lower():
                inbound_found = True
                settings = inbound.get('settings')
                if not settings:
                    inbound['settings'] = {
                        'clients': [client]
                    }
                    return config
                
                clients = settings.get('clients')
                if clients is None:
                    settings['clients'] = [client]
                else:
                    clients.append(client)
        
        if not inbound_found:
            raise ValueError(f"{protocol.capitalize()} inbound's not found")

        return config
    
    @staticmethod
    def load_temp_config(config_manager: ConfigManager):
        temp_config = config_manager.create_temp_config()
        return config_manager.load(temp_config), temp_config

class XrayManager:

    def __init__(self, config_manager: ConfigManager, service_manager: ServiceManager):
        self.config_manager = config_manager
        self.service_manager = service_manager

    
    def restart_xray(self):
        return self.service_manager.restart("xray")
    
    def status(self):
        return self.service_manager.status("xray")
    

    def apply_configuration(self, modified_config, temp_path, user):
        self.config_manager.save(modified_config, saving_path=temp_path, create_backup=False)
        result = self.service_manager.validate_xray(temp_path)

        if result.returncode != 0:
            self.config_manager.delete_temp_config(temp_path)
            raise Exception(f"Failed to validate the new config, Error: {result.stderr}")
        
        self.config_manager.replace_config(temp_path)
        self.restart_xray()

        config = {}
        with open("/etc/netx/netx.conf") as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                key, value = line.split("=", 1)
                config[key] = value

        domain = config["DOMAIN"]
        result_uri_80 = f"{user.protocol}://{user.uuid}@{domain}:80?type=ws&security=none&path=%2F{user.protocol}#{user.email}"
        result_uri_443 = f"{user.protocol}://{user.uuid}@{domain}:443?type=ws&security=tls&host={domain}&path=%2Fvless&sni={domain}#{user.email}"

        os.system('cls') if os.name == 'nt' else os.system('clear')
        print(f"{user.protocol} URI NON-TLS\n{result_uri_80}")
        print(f"\n{user.protocol} URI TLS\n{result_uri_443}")
    

    def add_vless_user(self, user:VlessUser):
        config, temp_path = XrayHelper.load_temp_config(self.config_manager)        
        modified_config = XrayHelper.add_client(config, user.to_dict(),'vless')

        self.apply_configuration(modified_config, temp_path, user)

    def add_vmess_user(self, user:VmessUser):
        config, temp_path = XrayHelper.load_temp_config(self.config_manager)        
        modified_config = XrayHelper.add_client(config, user.to_dict(),'vmess')

        self.apply_configuration(modified_config, temp_path, user)

    
    def add_trojan_user(self, user: TrojanUser):
        config, temp_path = XrayHelper.load_temp_config(self.config_manager)        
        modified_config = XrayHelper.add_client(config, user.to_dict(),'trojan')

        self.apply_configuration(modified_config, temp_path, user)

        