from entities.project import Project


class ProjectDataService:
    """Simple CRUD for the projects collection. No business logic here."""

    def __init__(self, collection):
        self.collection = collection

    def create(self, project: Project):
        self.collection.insert_one(project.to_dict())
        return project

    def get_by_project_id(self, project_id):
        doc = self.collection.find_one({"projectId": project_id})
        return Project.from_dict(doc) if doc else None

    def add_member(self, project_id, user_id):
        # $addToSet keeps members unique, so joining twice is harmless.
        self.collection.update_one(
            {"projectId": project_id}, {"$addToSet": {"members": user_id}}
        )

    def remove_member(self, project_id, user_id):
        self.collection.update_one({"projectId": project_id}, {"$pull": {"members": user_id}})

    def delete(self, project_id):
        return self.collection.delete_one({"projectId": project_id}).deleted_count > 0

    def list_for_user(self, user_id):
        return [Project.from_dict(d) for d in self.collection.find({"members": user_id})]
