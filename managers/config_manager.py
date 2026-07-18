import json,os
from datetime import datetime
import tempfile, pathlib, shutil

class ConfigManager:

    def __init__(self, config_path, backup_directory):
        self.config_path = config_path
        self.backup_directory = backup_directory
    
    def load(self, loading_path=None):
        loading_file = self.config_path if not loading_path else loading_path

        if(not pathlib.Path(loading_file).exists()):
            raise FileNotFoundError("Config file is not found")

        with open(loading_file, 'r') as f:
            return json.load(f)
    
    def save(self, updated_config, saving_path=None, create_backup=True):
        if create_backup:
            self.create_backup()
        
        saving_file = self.config_path if not saving_path else saving_path

        with open(saving_file, 'w') as f:
            json.dump(updated_config, f, indent=4)
    
    def create_backup(self):
        config = self.load()
        os.makedirs(self.backup_directory,exist_ok=True)
        with open(f"{self.backup_directory}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", 'w') as f:
            json.dump(config, f, indent=4)
    
    def create_temp_config(self):
        temp_path = pathlib.Path(tempfile.gettempdir()).joinpath("xray_config.json")
        shutil.copy(self.config_path, temp_path)
        
        return temp_path

    def replace_config(self, temp_path):
        if not pathlib.Path(temp_path).exists():
            raise FileNotFoundError("Config file does not exists")
    
        if pathlib.Path(self.config_path).exists():
            os.remove(self.config_path)
        
        shutil.move(temp_path, self.config_path)

    def delete_temp_config(self, temp_path):
        if pathlib.Path(temp_path).exists():
            os.remove(temp_path)