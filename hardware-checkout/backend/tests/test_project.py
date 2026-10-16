import pytest
from fastapi.testclient import TestClient

from controllers.project_controller import get_project_service
from main import app
from services.project_service import ProjectService, ProjectServiceError


class FakeProjectDataService:
    """Stands in for MongoDB so tests run offline."""

    def __init__(self):
        self.projects = {}

    def create(self, project):
        self.projects[project.projectId] = project
        return project

    def get_by_project_id(self, project_id):
        return self.projects.get(project_id)

    def add_member(self, project_id, user_id):
        p = self.projects[project_id]
        if user_id not in p.members:
            p.members.append(user_id)

    def list_for_user(self, user_id):
        return [p for p in self.projects.values() if user_id in p.members]


@pytest.fixture
def fake_db():
    return FakeProjectDataService()


@pytest.fixture
def service(fake_db):
    return ProjectService(fake_db)


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_project_service] = lambda: ProjectService(fake_db)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_adds_creator_as_member(service):
    p = service.create("asamant", "p1", "Sensors", "desc")
    assert p.members == ["asamant"]


def test_create_duplicate_project_id(service):
    service.create("asamant", "p1", "Sensors")
    with pytest.raises(ProjectServiceError) as e:
        service.create("bjha", "p1", "Other")
    assert e.value.status_code == 409


@pytest.mark.parametrize("uid,pid,name", [("", "p1", "n"), ("u", "", "n"), ("u", "p1", ""), ("u", "p 1", "n")])
def test_create_invalid_input(service, uid, pid, name):
    with pytest.raises(ProjectServiceError) as e:
        service.create(uid, pid, name)
    assert e.value.status_code == 400


def test_join_existing_project(service):
    service.create("asamant", "p1", "Sensors")
    p = service.join("bjha", "p1")
    assert p.members == ["asamant", "bjha"]


def test_join_twice_does_not_duplicate(service):
    service.create("asamant", "p1", "Sensors")
    service.join("bjha", "p1")
    assert service.join("bjha", "p1").members.count("bjha") == 1


def test_join_unknown_project(service):
    with pytest.raises(ProjectServiceError) as e:
        service.join("bjha", "nope")
    assert e.value.status_code == 404


def test_list_only_returns_users_projects(service):
    service.create("asamant", "p1", "A")
    service.create("bjha", "p2", "B")
    assert [p.projectId for p in service.list_for_user("asamant")] == ["p1"]


def test_create_endpoint(client):
    res = client.post("/projects", json={"userId": "u", "projectId": "p1", "name": "A", "description": "d"})
    assert res.status_code == 201
    assert res.json()["members"] == ["u"]


def test_join_and_list_endpoints(client):
    client.post("/projects", json={"userId": "u", "projectId": "p1", "name": "A"})
    assert client.post("/projects/join", json={"userId": "v", "projectId": "p1"}).status_code == 200
    assert client.post("/projects/join", json={"userId": "v", "projectId": "zzz"}).status_code == 404
    res = client.get("/projects", params={"userId": "v"})
    assert [p["projectId"] for p in res.json()] == ["p1"]
