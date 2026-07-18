import subprocess,pathlib

class ServiceManager:

    def restart(self, service_name):
        return subprocess.run(
            ["systemctl","restart",service_name],
            text=True,
            capture_output=True
        )
    
    def status(self, service_name):
        return subprocess.run(
            ["systemctl","is-active",service_name],
            text=True,
            capture_output=True
        )

    def validate_xray(self, config_path):

        if(not pathlib.Path(config_path).exists()):
            raise FileNotFoundError("Config path does not exists")

        return subprocess.run(
            ["xray", "run", "-test", "-config", config_path],
            text=True,
            capture_output=True
        )
    
