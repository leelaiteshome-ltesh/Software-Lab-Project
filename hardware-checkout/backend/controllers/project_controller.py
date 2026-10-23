from fastapi import APIRouter, Depends, HTTPException

from dataservices.hardware_dataservice import HardwareDataService
from dataservices.project_dataservice import ProjectDataService
from dataservices.user_dataservice import UserDataService
from db import get_database, get_hardware_database, get_projects_database
from entities.project import (
    CreateProjectRequest,
    JoinProjectRequest,
    MessageResponse,
    Project,
    UserRequest,
)
from services.project_service import ProjectService, ProjectServiceError

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service():
    return ProjectService(
        ProjectDataService(get_projects_database()["projects"]),
        UserDataService(get_database()["users"]),
        HardwareDataService(get_hardware_database()),
    )


def _run(fn, *args):
    try:
        return fn(*args)
    except ProjectServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("", response_model=Project, status_code=201)
def create_project(body: CreateProjectRequest, service: ProjectService = Depends(get_project_service)):
    return _run(service.create, body.userId, body.projectId, body.name, body.description)


@router.post("/join", response_model=Project)
def join_project(body: JoinProjectRequest, service: ProjectService = Depends(get_project_service)):
    return _run(service.join, body.userId, body.projectId)


@router.get("", response_model=list[Project])
def my_projects(userId: str, service: ProjectService = Depends(get_project_service)):
    return _run(service.list_for_user, userId)


@router.get("/{projectId}", response_model=Project)
def get_project(projectId: str, userId: str, service: ProjectService = Depends(get_project_service)):
    """Members only."""
    return _run(service.get_for_member, userId, projectId)


@router.post("/{projectId}/leave", response_model=MessageResponse)
def leave_project(projectId: str, body: UserRequest, service: ProjectService = Depends(get_project_service)):
    """Members can leave. The owner can't."""
    _run(service.leave, body.userId, projectId)
    return MessageResponse(message="Left project")


@router.delete("/{projectId}/members/{memberId}", response_model=Project)
def remove_member(
    projectId: str, memberId: str, userId: str, service: ProjectService = Depends(get_project_service)
):
    """Owner only. `userId` is the owner making the request."""
    return _run(service.remove_member, userId, projectId, memberId)


@router.delete("/{projectId}", response_model=MessageResponse)
def delete_project(projectId: str, userId: str, service: ProjectService = Depends(get_project_service)):
    """Owner only. Blocked while the project has hardware checked out."""
    _run(service.delete, userId, projectId)
    return MessageResponse(message="Project deleted")
