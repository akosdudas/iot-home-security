import os
import json
import pyrebase

def setup_firebase_app(config_file_path):
    with open(config_file_path) as config_file:
        config = json.load(config_file)
    
    return pyrebase.initialize_app(config)

__config_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..',
    '..',
    'config', 'gcp', 'firebase.json'
)

firebase = setup_firebase_app(__config_path)
pass