import requests
from requests_jwt import JWTAuth
from auth import Auth
from utils import get_functions_base_url

def send_notification(title, body):
    token = Auth().get_token()
    if not token:
        # TODO find a better exception type
        raise BaseException('Device must be logged in to send nofitications')

    cloud_function_url = '/'.join([
        get_functions_base_url(), 
        'device_actions', 
        'send_push_notification'
    ])

    res = requests.post(
        cloud_function_url,
        json={
            'title': title,
            'body': body
        }, 
        headers={
            "authorization": "Bearer " + token
        }
    )
    if res.status_code == 200:
        return True
    else:
        return False
