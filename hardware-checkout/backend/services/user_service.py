from entities.user import User
from utils.encryption import encrypt

# Cipher settings from the class HW
N = 3
D = 1


class UserServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UserService:
    """Business logic for users. Talks to the dataservice, never to MongoDB directly."""

    def __init__(self, dataservice):
        self.dataservice = dataservice

    def _validate(self, user_id, password):
        if not user_id or not password:
            raise UserServiceError("userId and password are required", 400)
        if " " in user_id or "!" in user_id:
            raise UserServiceError("userId can't contain spaces or '!'", 400)
        try:
            encrypt(password, N, D)
        except ValueError:
            raise UserServiceError("Password can't contain spaces or '!'", 400)

    def sign_up(self, user_id, password):
        self._validate(user_id, password)
        if self.dataservice.get_by_user_id(user_id):
            raise UserServiceError("User already exists", 409)
        user = User(userId=user_id, password=encrypt(password, N, D))
        self.dataservice.create(user)
        return user

    def login(self, user_id, password):
        if not user_id or not password:
            raise UserServiceError("userId and password are required", 400)
        user = self.dataservice.get_by_user_id(user_id)
        try:
            matches = user is not None and user.password == encrypt(password, N, D)
        except ValueError:
            matches = False
        if not matches:
            raise UserServiceError("Invalid userId or password", 401)
        return user
