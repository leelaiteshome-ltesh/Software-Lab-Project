import re
from datetime import datetime, timezone

from entities.project import Project

# 3-20 chars: starts with a letter, then letters, numbers, '-' or '_'.
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,19}$")
PROJECT_ID_RULES = (
    "ProjectID must be 3-20 characters, start with a letter, "
    "and use only letters, numbers, '-' or '_'"
)
NAME_MAX = 50
DESCRIPTION_MAX = 200


class ProjectServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProjectService:
    """Business logic for projects. Talks to the dataservices, never to MongoDB directly.

    `user_dataservice` is used to check that userIds belong to real accounts.
    `hardware_dataservice` is used to stop a project being deleted while it
    still has hardware checked out. Both are optional so tests can skip them.
    """

    def __init__(self, dataservice, user_dataservice=None, hardware_dataservice=None):
        self.dataservice = dataservice
        self.users = user_dataservice
        self.hardware = hardware_dataservice

    # ---- helpers ----

    def _require_user(self, user_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        if self.users is not None and self.users.get_by_user_id(user_id) is None:
            raise ProjectServiceError("User not found", 404)

    def _get_project(self, project_id):
        project_id = (project_id or "").strip()
        if not project_id:
            raise ProjectServiceError("projectID is required", 400)
        project = self.dataservice.get_by_project_id(project_id)
        if project is None:
            raise ProjectServiceError("Project not found", 404)
        return project

    # ---- actions ----

    def create(self, user_id, project_id, name, description=""):
        project_id = (project_id or "").strip()
        name = (name or "").strip()
        description = (description or "").strip()

        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        if not project_id or not name:
            raise ProjectServiceError("Project name and projectID are required", 400)
        if not PROJECT_ID_PATTERN.match(project_id):
            raise ProjectServiceError(PROJECT_ID_RULES, 400)
        if len(name) > NAME_MAX:
            raise ProjectServiceError(f"Project name can be at most {NAME_MAX} characters", 400)
        if len(description) > DESCRIPTION_MAX:
            raise ProjectServiceError(f"Description can be at most {DESCRIPTION_MAX} characters", 400)
        self._require_user(user_id)
        if self.dataservice.get_by_project_id(project_id):
            raise ProjectServiceError("A project with that projectID already exists", 409)

        project = Project(
            projectId=project_id,
            name=name,
            description=description,
            owner=user_id,
            members=[user_id],
            createdAt=datetime.now(timezone.utc),
        )
        created = self.dataservice.create(project)
        if created is None:  # lost a race with someone creating the same ID
            raise ProjectServiceError("A project with that projectID already exists", 409)
        return created

    def join(self, user_id, project_id):
        self._require_user(user_id)
        project = self._get_project(project_id)
        if user_id not in project.members:
            self.dataservice.add_member(project.projectId, user_id)
            project = self.dataservice.get_by_project_id(project.projectId)
        return project

    def get_for_member(self, user_id, project_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        project = self._get_project(project_id)
        if user_id not in project.members:
            raise ProjectServiceError("You're not a member of this project", 403)
        return project

    def leave(self, user_id, project_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        project = self._get_project(project_id)
        if user_id not in project.members:
            raise ProjectServiceError("You're not a member of this project", 400)
        if user_id == project.owner:
            raise ProjectServiceError("The owner can't leave their own project. Delete it instead.", 400)
        self.dataservice.remove_member(project.projectId, user_id)

    def remove_member(self, owner_id, project_id, member_id):
        if not owner_id or not member_id:
            raise ProjectServiceError("userId and memberId are required", 400)
        project = self._get_project(project_id)
        if owner_id != project.owner:
            raise ProjectServiceError("Only the project owner can remove members", 403)
        if member_id == project.owner:
            raise ProjectServiceError("The owner can't be removed", 400)
        if member_id not in project.members:
            raise ProjectServiceError("That user isn't a member of this project", 404)
        self.dataservice.remove_member(project.projectId, member_id)
        return self.dataservice.get_by_project_id(project.projectId)

    def delete(self, user_id, project_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        project = self._get_project(project_id)
        if user_id != project.owner:
            raise ProjectServiceError("Only the project owner can delete this project", 403)
        if self.hardware is not None and self.hardware.get_project_checkouts(project.projectId):
            raise ProjectServiceError("Check in all hardware before deleting this project", 409)
        self.dataservice.delete(project.projectId)

    def list_for_user(self, user_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        return self.dataservice.list_for_user(user_id)
