from entities.project import Project


class ProjectServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProjectService:
    """Business logic for projects. Talks to dataservices, never to MongoDB directly.

    Rules:
      - ProjectID, name and description are validated
      - The creator must be a real user, and becomes owner + first member
      - Only the owner can remove members or delete the project
      - The owner can't leave their own project
      - A project can't be deleted while it still holds hardware
    """

    MAX_PROJECT_ID = 40
    MAX_NAME = 80
    MAX_DESCRIPTION = 500

    def __init__(self, dataservice, user_dataservice, hardware_dataservice):
        self.dataservice = dataservice
        self.users = user_dataservice
        self.hardware = hardware_dataservice

    # ---------- helpers ----------

    def _require_real_user(self, user_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        if self.users.get_by_user_id(user_id) is None:
            raise ProjectServiceError("User not found", 404)

    def _get_project(self, project_id):
        project = self.dataservice.get_by_project_id((project_id or "").strip())
        if project is None:
            raise ProjectServiceError("Project not found", 404)
        return project

    def _require_member(self, project, user_id):
        if user_id not in project.members:
            raise ProjectServiceError("You're not a member of this project", 403)

    def _require_owner(self, project, user_id):
        if project.owner != user_id:
            raise ProjectServiceError("Only the project owner can do that", 403)

    # ---------- create / join / list / get ----------

    def create(self, user_id, project_id, name, description=""):
        project_id = (project_id or "").strip()
        name = (name or "").strip()
        description = (description or "").strip()
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        if not project_id or not name:
            raise ProjectServiceError("Project name and projectID are required", 400)
        if any(c.isspace() for c in project_id):
            raise ProjectServiceError("projectID can't contain spaces", 400)
        if len(project_id) > self.MAX_PROJECT_ID:
            raise ProjectServiceError(f"projectID must be {self.MAX_PROJECT_ID} characters or fewer", 400)
        if len(name) > self.MAX_NAME:
            raise ProjectServiceError(f"Name must be {self.MAX_NAME} characters or fewer", 400)
        if len(description) > self.MAX_DESCRIPTION:
            raise ProjectServiceError(f"Description must be {self.MAX_DESCRIPTION} characters or fewer", 400)
        self._require_real_user(user_id)
        if self.dataservice.get_by_project_id(project_id):
            raise ProjectServiceError("A project with that projectID already exists", 409)
        project = Project(
            projectId=project_id,
            name=name,
            description=description,
            owner=user_id,
            members=[user_id],
            createdAt=Project.now(),
        )
        return self.dataservice.create(project)

    def join(self, user_id, project_id):
        if not user_id or not project_id:
            raise ProjectServiceError("userId and projectID are required", 400)
        self._require_real_user(user_id)
        project = self._get_project(project_id)
        if user_id not in project.members:
            self.dataservice.add_member(project.projectId, user_id)
            project = self.dataservice.get_by_project_id(project.projectId)
        return project

    def list_for_user(self, user_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        return self.dataservice.list_for_user(user_id)

    def get(self, user_id, project_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        project = self._get_project(project_id)
        self._require_member(project, user_id)
        return project

    # ---------- leave / remove / delete ----------

    def leave(self, user_id, project_id):
        project = self.get(user_id, project_id)
        if project.owner == user_id:
            raise ProjectServiceError("The owner can't leave their own project. Delete it instead.", 400)
        self.dataservice.remove_member(project.projectId, user_id)

    def remove_member(self, user_id, project_id, member_id):
        project = self.get(user_id, project_id)
        self._require_owner(project, user_id)
        if member_id == project.owner:
            raise ProjectServiceError("The owner can't be removed", 400)
        if member_id not in project.members:
            raise ProjectServiceError("That user isn't a member of this project", 404)
        self.dataservice.remove_member(project.projectId, member_id)
        return self.dataservice.get_by_project_id(project.projectId)

    def delete(self, user_id, project_id):
        project = self.get(user_id, project_id)
        self._require_owner(project, user_id)
        if self.hardware.project_holds_hardware(project.projectId):
            raise ProjectServiceError("Check in all hardware before deleting the project", 409)
        self.dataservice.delete(project.projectId)
        self.hardware.delete_checkouts_for_project(project.projectId)
