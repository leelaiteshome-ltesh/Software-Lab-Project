import pytest
from fastapi.testclient import TestClient

from controllers.user_controller import get_user_service
from main import app
from services.user_service import UserService, UserServiceError
from utils.encryption import decrypt, encrypt


class FakeUserDataService:
    """Stands in for MongoDB so tests run offline."""

    def __init__(self):
        self.users = {}

    def create(self, user):
        self.users[user.userId] = user
        return user

    def get_by_user_id(self, user_id):
        return self.users.get(user_id)


@pytest.fixture
def fake_db():
    return FakeUserDataService()


@pytest.fixture
def service(fake_db):
    return UserService(fake_db)


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_user_service] = lambda: UserService(fake_db)
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- encryption ----------

def test_encrypt_hw_example():
    assert encrypt("TEST", 2, 1) == "VUGV"


def test_encrypt_wraps_around():
    assert encrypt("~", 1, 1) == '"'
    assert encrypt('"', 1, -1) == "~"


def test_decrypt_reverses_encrypt():
    for text in ["Temp123", "TheKing%^&", "$72messenger"]:
        assert decrypt(encrypt(text, 3, 1), 3, 1) == text


def test_encrypt_is_deterministic():
    assert encrypt("Temp123", 3, 1) == encrypt("Temp123", 3, 1)


@pytest.mark.parametrize("text,N,D", [("has space", 3, 1), ("bang!", 3, 1), ("ok", 0, 1), ("ok", 3, 2)])
def test_encrypt_rejects_invalid_input(text, N, D):
    with pytest.raises(ValueError):
        encrypt(text, N, D)


# ---------- service ----------

def test_sign_up_stores_encrypted_password(service, fake_db):
    service.sign_up("asamant", "Temp123")
    stored = fake_db.users["asamant"]
    assert stored.password != "Temp123"
    assert stored.password == encrypt("Temp123", 3, 1)


def test_sign_up_duplicate_user(service):
    service.sign_up("asamant", "Temp123")
    with pytest.raises(UserServiceError) as e:
        service.sign_up("asamant", "Other1")
    assert e.value.status_code == 409


@pytest.mark.parametrize("user_id,password", [("", "Temp123"), ("asamant", ""), ("Ally!", "God$12"), ("a b", "x")])
def test_sign_up_invalid_input(service, user_id, password):
    with pytest.raises(UserServiceError) as e:
        service.sign_up(user_id, password)
    assert e.value.status_code == 400


def test_login_success(service):
    service.sign_up("bjha", "$72messenger")
    assert service.login("bjha", "$72messenger").userId == "bjha"


def test_login_wrong_password(service):
    service.sign_up("bjha", "$72messenger")
    with pytest.raises(UserServiceError) as e:
        service.login("bjha", "wrong")
    assert e.value.status_code == 401


def test_login_unknown_user(service):
    with pytest.raises(UserServiceError) as e:
        service.login("nobody", "Temp123")
    assert e.value.status_code == 401


# ---------- endpoints ----------

def test_signup_endpoint(client):
    res = client.post("/users/signup", json={"userId": "aissa", "password": "TheKing%^&"})
    assert res.status_code == 201
    assert "password" not in res.json()


def test_signup_endpoint_duplicate(client):
    client.post("/users/signup", json={"userId": "aissa", "password": "TheKing%^&"})
    res = client.post("/users/signup", json={"userId": "aissa", "password": "TheKing%^&"})
    assert res.status_code == 409


def test_login_endpoint(client):
    client.post("/users/signup", json={"userId": "skharel", "password": "Life15$"})
    assert client.post("/users/login", json={"userId": "skharel", "password": "Life15$"}).status_code == 200
    assert client.post("/users/login", json={"userId": "skharel", "password": "nope"}).status_code == 401
