import json, os, sys, subprocess

CONFIG_PATH = "/opt/netx/configs/env.json"

class Helpers:

    @staticmethod
    def load_app_config():
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except FileNotFoundError as e:
            print("App config is not found")
            sys.exit(1)
    
    @staticmethod
    def modify_app_config(config: dict):
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)

        except FileNotFoundError as e:
            print("App config is not found")
            sys.exit(1)
    
    @staticmethod
    def is_port_listening( port:str ):
        result = subprocess.run(
            [ "sudo", "ss", "-tulpn", "|", "grep", f":{port}" ],
            text=True,
            capture_output=True
        )

        return True if result.returncode == 0 else False