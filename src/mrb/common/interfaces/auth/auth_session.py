class AuthSession:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthSession, cls).__new__(cls)
            cls._instance.token = None
            cls._instance.user_data = None
        return cls._instance

    def set_auth_data(self, token, user_data):
        self.token = token
        self.user_data = user_data

    def clear_auth_data(self):
        self.token = None
        self.user_data = None
