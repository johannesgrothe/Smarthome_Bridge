class UnknownClientException(Exception):
    def __init__(self, name: str):
        super(UnknownClientException, self).__init__(f"client with name: {name} does nee exist")


class AuthError(Exception):
    """Error raised if anything failed checking the authentication of an incoming request"""
