from fastapi import APIRouter, Depends, HTTPException, Response

from dataservices.hardware_dataservice import HardwareDataService
from dataservices.project_dataservice import ProjectDataService
from dataservices.user_dataservice import UserDataService
from db import get_database, get_hardware_database, get_projects_database
from entities.project import CreateProjectRequest, JoinProjectRequest, LeaveProjectRequest, Project
from services.project_service import ProjectService, ProjectServiceError

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service():
    hw_db = get_hardware_database()
    return ProjectService(
        ProjectDataService(get_projects_database()["projects"]),
        UserDataService(get_database()["users"]),
        HardwareDataService(hw_db["hardware_sets"], hw_db["checkouts"]),
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
    """Project details. Members only."""
    return _run(service.get, userId, projectId)


@router.post("/{projectId}/leave", status_code=204)
def leave_project(projectId: str, body: LeaveProjectRequest, service: ProjectService = Depends(get_project_service)):
    """A member leaves. The owner can't leave their own project."""
    _run(service.leave, body.userId, projectId)
    return Response(status_code=204)


@router.delete("/{projectId}/members/{memberId}", response_model=Project)
def remove_member(projectId: str, memberId: str, userId: str, service: ProjectService = Depends(get_project_service)):
    """Owner removes a member. `userId` is the person making the request."""
    return _run(service.remove_member, userId, projectId, memberId)


@router.delete("/{projectId}", status_code=204)
def delete_project(projectId: str, userId: str, service: ProjectService = Depends(get_project_service)):
    """Owner deletes the project. Blocked while any hardware is still checked out."""
    _run(service.delete, userId, projectId)
    return Response(status_code=204)
