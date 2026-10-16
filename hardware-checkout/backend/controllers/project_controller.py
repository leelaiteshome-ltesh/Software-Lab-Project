from fastapi import APIRouter, Depends, HTTPException

from dataservices.project_dataservice import ProjectDataService
from db import get_projects_database
from entities.project import CreateProjectRequest, JoinProjectRequest, Project
from services.project_service import ProjectService, ProjectServiceError

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service():
    return ProjectService(ProjectDataService(get_projects_database()["projects"]))


@router.post("", response_model=Project, status_code=201)
def create_project(body: CreateProjectRequest, service: ProjectService = Depends(get_project_service)):
    try:
        return service.create(body.userId, body.projectId, body.name, body.description)
    except ProjectServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/join", response_model=Project)
def join_project(body: JoinProjectRequest, service: ProjectService = Depends(get_project_service)):
    try:
        return service.join(body.userId, body.projectId)
    except ProjectServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("", response_model=list[Project])
def my_projects(userId: str, service: ProjectService = Depends(get_project_service)):
    try:
        return service.list_for_user(userId)
    except ProjectServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
