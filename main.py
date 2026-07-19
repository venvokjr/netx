from managers.xray_manager import XrayManager
from managers import config_manager, service_manager
from models.xray_users import VmessUser, VlessUser, TrojanUser
from utils import helpers
from datetime import datetime,timedelta
from utils import helpers
import os, psutil, traceback,json


CONFIG_MANAGER = ""
SERVICE_MANAGER = ""
XRAY_MANAGER = ""
DOMAIN = ""

def initialize():
    configs = helpers.Helpers.load_app_config()
    
    xray_config_path = configs['xray_config']
    backup_dir = configs['backup_dir']

    global CONFIG_MANAGER, SERVICE_MANAGER, XRAY_MANAGER, DOMAIN
    DOMAIN = configs['domain']
    CONFIG_MANAGER = config_manager.ConfigManager(xray_config_path, backup_dir)
    SERVICE_MANAGER = service_manager.ServiceManager()
    XRAY_MANAGER = XrayManager(CONFIG_MANAGER, SERVICE_MANAGER)

def clear():
    os.system('cls') if os.name == 'nt' else os.system('clear')

def printf(key:str, value:str):
    print(f"{key:<22} : {value}")

def get_uptime(total_seconds:timedelta):
    total_seconds = int(total_seconds.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days} days, {hours} hours, {minutes} mins, {seconds} secs"

def banner():
    with open("/etc/os-release") as f:
        info = {}
        for line in f:
            if "=" in line:
                k, v = line.rstrip().split("=", 1)
                info[k] = v.strip('"')

    ram = psutil.virtual_memory()

    print("="*50)
    print(f"{'OS':<22} : {info['PRETTY_NAME']}")
    print(f"{'Kernel':<22} : {os.uname().release}")
    print(f"{'Domain':<22} : {DOMAIN}")
    print(f"{'Hostname':<22} : {os.uname().nodename}")
    print(f"{'CPU Cores':<22} : {os.cpu_count()}")
    print(f"{'RAM':<22} : {ram.used // 1024**2} MB / {ram.total // 1024**2} MB")
    print(f"{'DATE':<22} : {datetime.now().strftime("%a, %d %b %Y %H:%M:%S")}")
    print(f"{'UPTIME':<22} : { get_uptime(datetime.now() - datetime.fromtimestamp(psutil.boot_time())) }")
    print("="*50)

def ssh_menu():
    print(f"{'THIS IS SSH MENU':>27}")

def collect_user_input():
    username = input("Enter username: ").strip()
    expiry = int(input("Enter duration(in days): ").strip())


    return username, expiry

def xray_menu():
    try:
        clear()
        print("="*50)
        print(f"{'THIS IS XRAY MENU':>27}")
        print("="*50)
        print("1. Add VMESS account")
        print("2. Add VLESS account")
        print("3. Add TROJAN account")
        choice = input("Select option: ")

        if choice == "1":
            username, expiry = collect_user_input()
            user = VmessUser(username, expiry)
            XRAY_MANAGER.add_vmess_user(user)
        
        elif choice == "2":
            username, expiry = collect_user_input()
            user = VlessUser(username, expiry)
            XRAY_MANAGER.add_vless_user(user)
        
        elif choice == "3":
            username, expiry = collect_user_input()
            user = TrojanUser(username, expiry)
            XRAY_MANAGER.add_trojan_user()
    except Exception:
        traceback.print_exc()

def script_menu():
    print(f"{'NETX MENU':>27}")
    print("="*50)

    print(f"{'[1•] SSH MENU':<20} {'[2•] XRAY MENU'}")

    choice = input("Select menu: ")

    if choice == "1":
        ssh_menu()
    elif choice == "2":
        xray_menu()
 

def main():
    clear()
    banner()
    script_menu()

if __name__ == "__main__":
    initialize()
    main()