from fastapi import APIRouter, Depends, HTTPException

from dataservices.hardware_dataservice import HardwareDataService
from dataservices.project_dataservice import ProjectDataService
from db import get_hardware_database, get_projects_database
from entities.hardware import HardwareRequest, HardwareResult, HardwareSet, ProjectHardware
from services.hardware_service import HardwareService, HardwareServiceError

router = APIRouter(prefix="/hardware", tags=["Hardware"])


def get_hardware_service():
    return HardwareService(
        HardwareDataService(get_hardware_database()),
        ProjectDataService(get_projects_database()["projects"]),
    )


def _run(fn, *args):
    try:
        return fn(*args)
    except HardwareServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("", response_model=list[HardwareSet])
def list_hardware_sets(service: HardwareService = Depends(get_hardware_service)):
    return service.list_sets()


@router.get("/projects/{projectId}", response_model=list[ProjectHardware])
def project_hardware(projectId: str, userId: str, service: HardwareService = Depends(get_hardware_service)):
    """What a project currently has checked out. Members only."""
    return _run(service.project_hardware, userId, projectId)


@router.post("/checkout", response_model=HardwareResult)
def check_out(body: HardwareRequest, service: HardwareService = Depends(get_hardware_service)):
    return _run(service.check_out, body.userId, body.projectId, body.hwSetId, body.quantity)


@router.post("/checkin", response_model=HardwareResult)
def check_in(body: HardwareRequest, service: HardwareService = Depends(get_hardware_service)):
    return _run(service.check_in, body.userId, body.projectId, body.hwSetId, body.quantity)
