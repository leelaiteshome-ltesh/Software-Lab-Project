from pymongo.errors import DuplicateKeyError, OperationFailure

from entities.project import Project


class ProjectDataService:
    """Simple CRUD for the projects collection. No business logic here."""

    def __init__(self, collection):
        self.collection = collection

    def ensure_indexes(self):
        """Run once on startup. Backfills the lowercase ID on older projects,
        then makes it unique so two projects can't share an ID in any case."""
        for doc in self.collection.find({"projectIdLower": {"$exists": False}}):
            self.collection.update_one(
                {"_id": doc["_id"]}, {"$set": {"projectIdLower": doc["projectId"].lower()}}
            )
        try:
            self.collection.create_index(
                "projectIdLower",
                unique=True,
                partialFilterExpression={"projectIdLower": {"$exists": True}},
            )
        except OperationFailure as e:
            print(f"WARNING: couldn't create unique projectId index: {e}")
        self.collection.create_index("members")

    def create(self, project: Project):
        """Returns None if the projectId is already taken."""
        try:
            self.collection.insert_one(project.to_dict())
        except DuplicateKeyError:
            return None
        return project

    def get_by_project_id(self, project_id):
        doc = self.collection.find_one({"projectIdLower": project_id.lower()})
        return Project.from_dict(doc) if doc else None

    def add_member(self, project_id, user_id):
        # $addToSet keeps members unique, so joining twice is harmless.
        self.collection.update_one(
            {"projectIdLower": project_id.lower()}, {"$addToSet": {"members": user_id}}
        )

    def remove_member(self, project_id, user_id):
        self.collection.update_one(
            {"projectIdLower": project_id.lower()}, {"$pull": {"members": user_id}}
        )

    def delete(self, project_id):
        result = self.collection.delete_one({"projectIdLower": project_id.lower()})
        return result.deleted_count > 0

    def list_for_user(self, user_id):
        return [Project.from_dict(d) for d in self.collection.find({"members": user_id})]
