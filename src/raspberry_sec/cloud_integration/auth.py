from firebase import firebase

class Auth:
    class __Auth:
        def __init__(self):
            self.user = None

        def log_in_user(self, user, password):
            user = firebase.auth().sign_in_with_email_and_password(user, password)
            self.user = user

        def get_token(self):
            if not self.user:
                return None

            return self.user['idToken']

        def refresh_token(self):
            self.user = firebase.auth().refresh(self.user['refreshToken'])

        def log_out_user(self):
            # Not implemented by pyrebase
            # Maybe the best way to do this would be to call a logout cloud function
            self.user = None
            pass
    
    instance = None
    def __init__(self):
        if not Auth.instance:
            Auth.instance = Auth.__Auth()
        else:
            pass
    
    def get_user(self):
        return Auth.instance.user

    def log_in_user(self, username, password):
        Auth.instance.log_in_user(username, password)

    def get_token(self):
        return Auth.instance.get_token()

    def refresh_token(self):
        Auth.instance.refresh_token()

def register_device():
    pass