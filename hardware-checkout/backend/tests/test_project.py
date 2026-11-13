import pytest
from fastapi.testclient import TestClient

from controllers.project_controller import get_project_service
from main import app
from services.project_service import ProjectService, ProjectServiceError
from tests.fakes import FakeHardwareDataService, FakeProjectDataService, FakeUserDataService

USERS = ["asamant", "bjha", "u", "v", "w"]


@pytest.fixture
def fake_db():
    return FakeProjectDataService()


@pytest.fixture
def fake_hw():
    hw = FakeHardwareDataService()
    hw.ensure_set("HWSet1", 100)
    return hw


@pytest.fixture
def service(fake_db, fake_hw):
    return ProjectService(fake_db, FakeUserDataService(USERS), fake_hw)


@pytest.fixture
def client(service):
    app.dependency_overrides[get_project_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def expect_error(status, fn, *args):
    with pytest.raises(ProjectServiceError) as e:
        fn(*args)
    assert e.value.status_code == status


# ---------- create ----------

def test_create_makes_creator_owner_and_first_member(service):
    p = service.create("asamant", "p1", "Sensors", "desc")
    assert p.owner == "asamant"
    assert p.members == ["asamant"]
    assert p.createdAt is not None


def test_create_requires_real_user(service):
    expect_error(404, service.create, "ghost", "p1", "Sensors")


def test_create_duplicate_project_id(service):
    service.create("asamant", "p1", "Sensors")
    expect_error(409, service.create, "bjha", "p1", "Other")


@pytest.mark.parametrize(
    "uid,pid,name,desc",
    [("", "p1", "n", ""), ("u", "", "n", ""), ("u", "p1", "", ""), ("u", "p 1", "n", ""),
     ("u", "x" * 41, "n", ""), ("u", "p1", "n" * 81, ""), ("u", "p1", "n", "d" * 501)],
)
def test_create_invalid_input(service, uid, pid, name, desc):
    expect_error(400, service.create, uid, pid, name, desc)


# ---------- join / list / get ----------

def test_join_existing_project(service):
    service.create("asamant", "p1", "Sensors")
    assert service.join("bjha", "p1").members == ["asamant", "bjha"]


def test_join_twice_does_not_duplicate(service):
    service.create("asamant", "p1", "Sensors")
    service.join("bjha", "p1")
    assert service.join("bjha", "p1").members.count("bjha") == 1


def test_join_unknown_project(service):
    expect_error(404, service.join, "bjha", "nope")


def test_list_only_returns_users_projects(service):
    service.create("asamant", "p1", "A")
    service.create("bjha", "p2", "B")
    assert [p.projectId for p in service.list_for_user("asamant")] == ["p1"]


def test_get_is_members_only(service):
    service.create("asamant", "p1", "A")
    assert service.get("asamant", "p1").name == "A"
    expect_error(403, service.get, "bjha", "p1")


# ---------- leave / remove / delete ----------

def test_member_can_leave(service):
    service.create("asamant", "p1", "A")
    service.join("bjha", "p1")
    service.leave("bjha", "p1")
    assert service.get("asamant", "p1").members == ["asamant"]


def test_owner_cannot_leave(service):
    service.create("asamant", "p1", "A")
    expect_error(400, service.leave, "asamant", "p1")


def test_only_owner_can_remove_member(service):
    service.create("asamant", "p1", "A")
    service.join("bjha", "p1")
    service.join("u", "p1")
    expect_error(403, service.remove_member, "bjha", "p1", "u")
    assert service.remove_member("asamant", "p1", "u").members == ["asamant", "bjha"]


def test_owner_cannot_be_removed(service):
    service.create("asamant", "p1", "A")
    expect_error(400, service.remove_member, "asamant", "p1", "asamant")


def test_only_owner_can_delete(service, fake_db):
    service.create("asamant", "p1", "A")
    service.join("bjha", "p1")
    expect_error(403, service.delete, "bjha", "p1")
    service.delete("asamant", "p1")
    assert fake_db.get_by_project_id("p1") is None


def test_delete_blocked_while_hardware_out(service, fake_hw):
    service.create("asamant", "p1", "A")
    fake_hw.add_to_project("p1", "HWSet1", 5)
    expect_error(409, service.delete, "asamant", "p1")
    fake_hw.remove_from_project("p1", "HWSet1", 5)
    service.delete("asamant", "p1")


# ---------- endpoints ----------

def test_create_endpoint(client):
    res = client.post("/projects", json={"userId": "u", "projectId": "p1", "name": "A", "description": "d"})
    assert res.status_code == 201
    assert res.json()["members"] == ["u"]
    assert res.json()["owner"] == "u"


def test_join_and_list_endpoints(client):
    client.post("/projects", json={"userId": "u", "projectId": "p1", "name": "A"})
    assert client.post("/projects/join", json={"userId": "v", "projectId": "p1"}).status_code == 200
    assert client.post("/projects/join", json={"userId": "v", "projectId": "zzz"}).status_code == 404
    res = client.get("/projects", params={"userId": "v"})
    assert [p["projectId"] for p in res.json()] == ["p1"]


def test_manage_endpoints(client):
    client.post("/projects", json={"userId": "u", "projectId": "p1", "name": "A"})
    client.post("/projects/join", json={"userId": "v", "projectId": "p1"})
    client.post("/projects/join", json={"userId": "w", "projectId": "p1"})

    assert client.get("/projects/p1", params={"userId": "v"}).status_code == 200
    assert client.post("/projects/p1/leave", json={"userId": "v"}).status_code == 204
    assert client.post("/projects/p1/leave", json={"userId": "u"}).status_code == 400

    res = client.delete("/projects/p1/members/w", params={"userId": "u"})
    assert res.status_code == 200 and res.json()["members"] == ["u"]

    assert client.delete("/projects/p1", params={"userId": "u"}).status_code == 204
    assert client.get("/projects/p1", params={"userId": "u"}).status_code == 404
