import yaml
from pathlib import Path

def load_config (config_path='config.yml'):
    try:
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except yaml. YAMLError as e:
        print(f"Error parsing configuration file: {e}")
    return

CONFIG = load_config()