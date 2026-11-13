import pytest
from fastapi.testclient import TestClient

from controllers.hardware_controller import get_hardware_service
from main import app
from services.hardware_service import HardwareService, HardwareServiceError
from services.project_service import ProjectService
from tests.fakes import FakeHardwareDataService, FakeProjectDataService, FakeUserDataService


@pytest.fixture
def fake_projects():
    projects = FakeProjectDataService()
    ps = ProjectService(projects, FakeUserDataService(["owner", "member", "outsider"]), FakeHardwareDataService())
    ps.create("owner", "p1", "Sensors")
    ps.join("member", "p1")
    ps.create("outsider", "p2", "Other")
    return projects


@pytest.fixture
def fake_hw():
    return FakeHardwareDataService()


@pytest.fixture
def service(fake_hw, fake_projects):
    return HardwareService(fake_hw, fake_projects, default_sets={"HWSet1": 100, "HWSet2": 50})


@pytest.fixture
def client(service):
    app.dependency_overrides[get_hardware_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def expect_error(status, fn, *args):
    with pytest.raises(HardwareServiceError) as e:
        fn(*args)
    assert e.value.status_code == status


def row(rows, hw):
    return next(r for r in rows if r.hwSetId == hw)


def test_sets_are_seeded(service):
    sets = service.list_sets()
    assert [(s.hwSetId, s.capacity, s.availability) for s in sets] == [("HWSet1", 100, 100), ("HWSet2", 50, 50)]


def test_seeding_does_not_reset_existing_sets(fake_hw, fake_projects):
    fake_hw.ensure_set("HWSet1", 100)
    fake_hw.take_from_pool("HWSet1", 30)
    s = HardwareService(fake_hw, fake_projects, default_sets={"HWSet1": 100})
    assert s.list_sets()[0].availability == 70


def test_check_out_and_in(service):
    rows = service.check_out("member", "p1", "HWSet1", 30)
    assert row(rows, "HWSet1").availability == 70
    assert row(rows, "HWSet1").checkedOut == 30

    rows = service.check_in("owner", "p1", "HWSet1", 10)
    assert row(rows, "HWSet1").availability == 80
    assert row(rows, "HWSet1").checkedOut == 20


def test_members_only(service):
    expect_error(403, service.check_out, "outsider", "p1", "HWSet1", 1)
    expect_error(403, service.for_project, "outsider", "p1")


def test_unknown_project_or_set(service):
    expect_error(404, service.check_out, "owner", "nope", "HWSet1", 1)
    expect_error(404, service.check_out, "owner", "p1", "HWSet9", 1)


@pytest.mark.parametrize("qty", [0, -3, 1.5, "abc", "", True])
def test_quantity_must_be_whole_number_at_least_1(service, qty):
    expect_error(400, service.check_out, "owner", "p1", "HWSet1", qty)


def test_quantity_accepts_numeric_strings(service):
    assert row(service.check_out("owner", "p1", "HWSet1", "5"), "HWSet1").checkedOut == 5


def test_cannot_take_more_than_available(service):
    service.check_out("outsider", "p2", "HWSet2", 45)
    expect_error(409, service.check_out, "owner", "p1", "HWSet2", 6)
    assert row(service.check_out("owner", "p1", "HWSet2", 5), "HWSet2").availability == 0


def test_cannot_return_more_than_project_holds(service):
    service.check_out("outsider", "p2", "HWSet1", 20)
    service.check_out("owner", "p1", "HWSet1", 5)
    # p2's units don't count toward what p1 can return
    expect_error(409, service.check_in, "owner", "p1", "HWSet1", 6)
    assert row(service.check_in("owner", "p1", "HWSet1", 5), "HWSet1").checkedOut == 0


def test_endpoints(client):
    assert [s["hwSetId"] for s in client.get("/hardware").json()] == ["HWSet1", "HWSet2"]

    res = client.post("/hardware/checkout", json={"userId": "owner", "projectId": "p1", "hwSetId": "HWSet1", "quantity": 7})
    assert res.status_code == 200

    rows = client.get("/hardware/projects/p1", params={"userId": "member"}).json()
    assert rows[0] == {"hwSetId": "HWSet1", "capacity": 100, "availability": 93, "checkedOut": 7}

    res = client.post("/hardware/checkin", json={"userId": "owner", "projectId": "p1", "hwSetId": "HWSet1", "quantity": 8})
    assert res.status_code == 409

    res = client.post("/hardware/checkout", json={"userId": "owner", "projectId": "p1", "hwSetId": "HWSet1", "quantity": 0})
    assert res.status_code == 400
