import pyrebase
from utils import get_firebase_config

def setup_firebase_app():
    config = get_firebase_config()
    return pyrebase.initialize_app(config)

firebase = setup_firebase_app()
