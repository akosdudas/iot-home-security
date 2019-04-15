import json
import os

__config_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..',
    '..',
    'config', 'gcp'
)

def get_gcp_config_dir():
    return __config_dir

def get_firebase_config():
    config = None
    config_file_path = os.path.join(get_gcp_config_dir(), 'firebase.json')
    with open(config_file_path) as config_file:
        config = json.load(config_file)
    
    return config

def get_functions_base_url():
    base_url = ""
    config_file_path = os.path.join(get_gcp_config_dir(), 'functions.json')
    with open(config_file_path) as config_file:
        config = json.load(config_file)
        base_url = config['BASE_URL']

    return base_url