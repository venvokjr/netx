import argparse
from utils import helpers
from managers import config_manager

def main():
    parser = argparse.ArgumentParser(description="Configuring the netx config")

    parser.add_argument(
        '--domain',
        type=str,
        required=False,
        help="The VPS Domain"
    )

    args = parser.parse_args()

    domain = str(args.domain)

    configs = helpers.Helpers.load_app_config()
    configs['domain'] = domain.strip()
    
    helpers.Helpers.modify_app_config(configs)

if __name__ == "__main__":
    main()