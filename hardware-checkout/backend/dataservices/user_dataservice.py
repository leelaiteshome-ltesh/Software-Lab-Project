from entities.user import User


class UserDataService:
    """Simple CRUD for the users collection. No business logic here."""

    def __init__(self, collection):
        self.collection = collection

    def create(self, user: User):
        self.collection.insert_one(user.to_dict())
        return user

    def get_by_user_id(self, user_id):
        doc = self.collection.find_one({"userId": user_id})
        return User.from_dict(doc) if doc else None

    def update(self, user: User):
        result = self.collection.update_one(
            {"userId": user.userId}, {"$set": {"password": user.password}}
        )
        return result.modified_count > 0

    def delete(self, user_id):
        result = self.collection.delete_one({"userId": user_id})
        return result.deleted_count > 0
