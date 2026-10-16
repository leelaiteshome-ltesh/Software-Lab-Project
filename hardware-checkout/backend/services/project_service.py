from entities.project import Project


class ProjectServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProjectService:
    """Business logic for projects. Talks to the dataservice, never to MongoDB directly."""

    def __init__(self, dataservice):
        self.dataservice = dataservice

    def create(self, user_id, project_id, name, description=""):
        project_id, name = (project_id or "").strip(), (name or "").strip()
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        if not project_id or not name:
            raise ProjectServiceError("Project name and projectID are required", 400)
        if " " in project_id:
            raise ProjectServiceError("projectID can't contain spaces", 400)
        if self.dataservice.get_by_project_id(project_id):
            raise ProjectServiceError("A project with that projectID already exists", 409)
        project = Project(
            projectId=project_id,
            name=name,
            description=(description or "").strip(),
            members=[user_id],
        )
        return self.dataservice.create(project)

    def join(self, user_id, project_id):
        if not user_id or not project_id:
            raise ProjectServiceError("userId and projectID are required", 400)
        project = self.dataservice.get_by_project_id(project_id.strip())
        if project is None:
            raise ProjectServiceError("Project not found", 404)
        if user_id not in project.members:
            self.dataservice.add_member(project.projectId, user_id)
            project = self.dataservice.get_by_project_id(project.projectId)
        return project

    def list_for_user(self, user_id):
        if not user_id:
            raise ProjectServiceError("userId is required", 400)
        return self.dataservice.list_for_user(user_id)
