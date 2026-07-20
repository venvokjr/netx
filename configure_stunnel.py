from utils import helpers
from managers import config_manager, service_manager
from pathlib import Path
import sys


def configure_stunnel_configuration():
    try:
        configs = helpers.Helpers.load_app_config()
        
        stunnel_port = configs['stunnel_port']
        config = configs['stunnel_config']

        serviceManager = service_manager.ServiceManager()


        CONFIGURATION = f"""
        cert = /etc/stunnel/stunnel.pem
        [ssh]

        accept = 443

        connect = 127.0.0.1:{stunnel_port}
        """

        generate_stunnel_pem(configs['domain'])
        save_config(CONFIGURATION, config)
        serviceManager.restart('stunnel4')

        result = serviceManager.status('stunnel4')
        if result.returncode == 0:
            print(f"Stunnel is configured properly and working")
            sys.exit(0)

        print("Stunnel is not active")
        sys.exit(1)

    except Exception as e:
        print(e)
        sys.exit(1)

def save_config(data, path):
    with open(path, 'w') as f:
        f.write(data)

def generate_stunnel_pem(domain: str):
    letsencrypt_dir = Path(f"/etc/letsencrypt/live/{domain}")

    fullchain = letsencrypt_dir / "fullchain.pem"
    privkey = letsencrypt_dir / "privkey.pem"
    stunnel_pem = Path("/etc/stunnel/stunnel.pem")

    if not fullchain.exists():
        raise FileNotFoundError(fullchain)

    if not privkey.exists():
        raise FileNotFoundError(privkey)

    with open(stunnel_pem, "wb") as outfile:
        with open(fullchain, "rb") as cert:
            outfile.write(cert.read())

        with open(privkey, "rb") as key:
            outfile.write(key.read())

    print("stunnel.pem generated successfully")

if __name__ == "__main__":
    configure_stunnel_configuration()