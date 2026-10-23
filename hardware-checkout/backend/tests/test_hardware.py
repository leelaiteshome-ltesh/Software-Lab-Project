import pytest
from fastapi.testclient import TestClient

from controllers.hardware_controller import get_hardware_service
from main import app
from services.hardware_service import HardwareService, HardwareServiceError
from services.project_service import ProjectService
from tests.fakes import FakeHardwareDataService, FakeProjectDataService


@pytest.fixture
def projects():
    ds = FakeProjectDataService()
    ps = ProjectService(ds)
    ps.create("owner", "proj1", "One")
    ps.join("member", "proj1")
    ps.create("other", "proj2", "Two")
    return ds


@pytest.fixture
def hw():
    return FakeHardwareDataService()


@pytest.fixture
def service(hw, projects):
    return HardwareService(hw, projects)


@pytest.fixture
def client(service):
    app.dependency_overrides[get_hardware_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def code(fn, *args):
    with pytest.raises(HardwareServiceError) as e:
        fn(*args)
    return e.value.status_code


def test_list_default_sets(service):
    sets = service.list_sets()
    assert [(s.hwSetId, s.capacity, s.availability) for s in sets] == [("HWSet1", 100, 100), ("HWSet2", 100, 100)]


def test_check_out_and_in(service):
    r = service.check_out("owner", "proj1", "HWSet1", 30)
    assert r.hardwareSet.availability == 70
    assert r.projectQuantity == 30
    r = service.check_in("member", "proj1", "HWSet1", 10)  # any member can check in
    assert r.hardwareSet.availability == 80
    assert r.projectQuantity == 20
    assert [(h.hwSetId, h.quantity) for h in service.project_hardware("owner", "proj1")] == [("HWSet1", 20)]


def test_cannot_check_out_more_than_available(service):
    service.check_out("owner", "proj1", "HWSet1", 90)
    assert code(service.check_out, "other", "proj2", "HWSet1", 11) == 400
    assert service.list_sets()[0].availability == 10  # unchanged by failed attempt


def test_can_check_out_exactly_whats_left(service):
    assert service.check_out("owner", "proj1", "HWSet2", 100).hardwareSet.availability == 0


def test_cannot_check_in_more_than_project_has(service):
    service.check_out("owner", "proj1", "HWSet1", 5)
    assert code(service.check_in, "owner", "proj1", "HWSet1", 6) == 400
    assert code(service.check_in, "other", "proj2", "HWSet1", 1) == 400  # proj2 has none


def test_projects_are_tracked_separately(service):
    service.check_out("owner", "proj1", "HWSet1", 5)
    service.check_out("other", "proj2", "HWSet1", 7)
    assert service.list_sets()[0].availability == 88
    assert service.project_hardware("other", "proj2")[0].quantity == 7


def test_non_member_is_blocked(service):
    assert code(service.check_out, "other", "proj1", "HWSet1", 1) == 403
    assert code(service.project_hardware, "other", "proj1") == 403


@pytest.mark.parametrize("qty", [0, -1, True])
def test_bad_quantity(service, qty):
    assert code(service.check_out, "owner", "proj1", "HWSet1", qty) == 400


def test_unknown_set_or_project(service):
    assert code(service.check_out, "owner", "proj1", "HWSet9", 1) == 404
    assert code(service.check_out, "owner", "nope", "HWSet1", 1) == 404


def test_project_id_lookup_is_case_insensitive(service):
    service.check_out("owner", "PROJ1", "HWSet1", 3)
    assert service.project_hardware("owner", "proj1")[0].quantity == 3


def test_endpoints(client):
    assert len(client.get("/hardware").json()) == 2
    body = {"userId": "owner", "projectId": "proj1", "hwSetId": "HWSet1", "quantity": 4}
    res = client.post("/hardware/checkout", json=body)
    assert res.status_code == 200
    assert res.json()["hardwareSet"]["availability"] == 96
    assert client.get("/hardware/projects/proj1", params={"userId": "member"}).json() == [
        {"hwSetId": "HWSet1", "quantity": 4}
    ]
    assert client.post("/hardware/checkin", json={**body, "quantity": 5}).status_code == 400
    assert client.post("/hardware/checkin", json=body).json()["projectQuantity"] == 0
    assert client.post("/hardware/checkout", json={**body, "quantity": 1.5}).status_code == 422
