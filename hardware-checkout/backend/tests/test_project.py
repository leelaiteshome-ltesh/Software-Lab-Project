import pytest
from fastapi.testclient import TestClient

from controllers.project_controller import get_project_service
from main import app
from services.project_service import ProjectService, ProjectServiceError
from tests.fakes import FakeHardwareDataService, FakeProjectDataService, FakeUserDataService

USERS = ["asamant", "bjha", "cli", "u", "v"]


@pytest.fixture
def fake_db():
    return FakeProjectDataService()


@pytest.fixture
def fake_hw():
    return FakeHardwareDataService()


@pytest.fixture
def service(fake_db, fake_hw):
    return ProjectService(fake_db, FakeUserDataService(USERS), fake_hw)


@pytest.fixture
def client(service):
    app.dependency_overrides[get_project_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def code(fn, *args):
    with pytest.raises(ProjectServiceError) as e:
        fn(*args)
    return e.value.status_code


# ---- create / project ID rules ----


def test_create_sets_owner_and_first_member(service):
    p = service.create("asamant", "sensor-1", "Sensors", "desc")
    assert p.owner == "asamant"
    assert p.members == ["asamant"]
    assert p.createdAt is not None


def test_create_duplicate_project_id(service):
    service.create("asamant", "proj1", "Sensors")
    assert code(service.create, "bjha", "proj1", "Other") == 409


def test_project_id_is_case_insensitive(service):
    service.create("asamant", "Proj-1", "Sensors")
    assert code(service.create, "bjha", "proj-1", "Other") == 409
    assert service.join("bjha", "PROJ-1").projectId == "Proj-1"


@pytest.mark.parametrize("pid", ["abc", "a_b-c", "Proj123", "a" * 20])
def test_valid_project_ids(service, pid):
    assert service.create("asamant", pid, "Name").projectId == pid


@pytest.mark.parametrize("pid", ["ab", "a" * 21, "1abc", "-abc", "has space", "bad!", "proj.1", "proj/1"])
def test_invalid_project_ids(service, pid):
    assert code(service.create, "asamant", pid, "Name") == 400


@pytest.mark.parametrize(
    "uid,pid,name,desc",
    [("", "proj1", "n", ""), ("u", "", "n", ""), ("u", "proj1", "", ""), ("u", "proj1", "   ", ""),
     ("u", "proj1", "x" * 51, ""), ("u", "proj1", "n", "x" * 201)],
)
def test_create_invalid_input(service, uid, pid, name, desc):
    assert code(service.create, uid, pid, name, desc) == 400


def test_create_unknown_user(service):
    assert code(service.create, "ghost", "proj1", "Name") == 404


# ---- join / list / get ----


def test_join_existing_project(service):
    service.create("asamant", "proj1", "Sensors")
    p = service.join("bjha", "proj1")
    assert p.members == ["asamant", "bjha"]
    assert p.owner == "asamant"


def test_join_twice_does_not_duplicate(service):
    service.create("asamant", "proj1", "Sensors")
    service.join("bjha", "proj1")
    assert service.join("bjha", "proj1").members.count("bjha") == 1


def test_join_unknown_project_or_user(service):
    service.create("asamant", "proj1", "Sensors")
    assert code(service.join, "bjha", "nope") == 404
    assert code(service.join, "ghost", "proj1") == 404


def test_list_only_returns_users_projects(service):
    service.create("asamant", "proj1", "A")
    service.create("bjha", "proj2", "B")
    assert [p.projectId for p in service.list_for_user("asamant")] == ["proj1"]


def test_get_project_members_only(service):
    service.create("asamant", "proj1", "A")
    assert service.get_for_member("asamant", "proj1").name == "A"
    assert code(service.get_for_member, "bjha", "proj1") == 403


# ---- owner vs member ----


def test_member_can_leave(service):
    service.create("asamant", "proj1", "A")
    service.join("bjha", "proj1")
    service.leave("bjha", "proj1")
    assert service.list_for_user("bjha") == []


def test_owner_cannot_leave(service):
    service.create("asamant", "proj1", "A")
    assert code(service.leave, "asamant", "proj1") == 400


def test_non_member_cannot_leave(service):
    service.create("asamant", "proj1", "A")
    assert code(service.leave, "bjha", "proj1") == 400


def test_owner_can_remove_member(service):
    service.create("asamant", "proj1", "A")
    service.join("bjha", "proj1")
    p = service.remove_member("asamant", "proj1", "bjha")
    assert p.members == ["asamant"]


def test_member_cannot_remove_others(service):
    service.create("asamant", "proj1", "A")
    service.join("bjha", "proj1")
    service.join("cli", "proj1")
    assert code(service.remove_member, "bjha", "proj1", "cli") == 403


def test_owner_cannot_remove_self_or_non_member(service):
    service.create("asamant", "proj1", "A")
    assert code(service.remove_member, "asamant", "proj1", "asamant") == 400
    assert code(service.remove_member, "asamant", "proj1", "bjha") == 404


def test_only_owner_can_delete(service):
    service.create("asamant", "proj1", "A")
    service.join("bjha", "proj1")
    assert code(service.delete, "bjha", "proj1") == 403
    service.delete("asamant", "proj1")
    assert code(service.join, "bjha", "proj1") == 404


def test_cannot_delete_with_hardware_out(service, fake_hw):
    service.create("asamant", "proj1", "A")
    fake_hw.add_to_project("proj1", "HWSet1", 5)
    assert code(service.delete, "asamant", "proj1") == 409


# ---- endpoints ----


def test_create_endpoint(client):
    res = client.post("/projects", json={"userId": "u", "projectId": "proj1", "name": "A", "description": "d"})
    assert res.status_code == 201
    assert res.json()["owner"] == "u"
    assert res.json()["members"] == ["u"]


def test_join_and_list_endpoints(client):
    client.post("/projects", json={"userId": "u", "projectId": "proj1", "name": "A"})
    assert client.post("/projects/join", json={"userId": "v", "projectId": "proj1"}).status_code == 200
    assert client.post("/projects/join", json={"userId": "v", "projectId": "zzz"}).status_code == 404
    res = client.get("/projects", params={"userId": "v"})
    assert [p["projectId"] for p in res.json()] == ["proj1"]


def test_owner_endpoints(client):
    client.post("/projects", json={"userId": "u", "projectId": "proj1", "name": "A"})
    client.post("/projects/join", json={"userId": "v", "projectId": "proj1"})
    assert client.get("/projects/proj1", params={"userId": "v"}).status_code == 200
    assert client.delete("/projects/proj1", params={"userId": "v"}).status_code == 403
    assert client.delete("/projects/proj1/members/v", params={"userId": "u"}).json()["members"] == ["u"]
    assert client.post("/projects/proj1/leave", json={"userId": "u"}).status_code == 400
    assert client.delete("/projects/proj1", params={"userId": "u"}).status_code == 200
    assert client.get("/projects/proj1", params={"userId": "u"}).status_code == 404
