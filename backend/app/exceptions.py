class UserNotFoundError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass


class OAuthError(Exception):
    pass


class InvalidTokenError(Exception):
    pass
