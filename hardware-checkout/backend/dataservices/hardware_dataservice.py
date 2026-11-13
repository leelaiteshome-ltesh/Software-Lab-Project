from entities.hardware import Checkout, HardwareSet


class HardwareDataService:
    """CRUD for the hardware database. No business logic here.

    Two collections:
      hardware_sets  {hwSetId, capacity, availability}
      checkouts      {projectId, hwSetId, quantity}

    The take/return methods use conditional updates so two people clicking
    at the same time can't push availability below 0 or a project's
    holding below 0.
    """

    def __init__(self, sets_collection, checkouts_collection):
        self.sets = sets_collection
        self.checkouts = checkouts_collection

    # ---------- hardware sets ----------

    def ensure_set(self, hw_set_id, capacity):
        """Create the set with full availability if it doesn't exist yet."""
        self.sets.update_one(
            {"hwSetId": hw_set_id},
            {"$setOnInsert": {"hwSetId": hw_set_id, "capacity": capacity, "availability": capacity}},
            upsert=True,
        )

    def list_sets(self):
        return [HardwareSet.from_dict(d) for d in self.sets.find().sort("hwSetId", 1)]

    def get_set(self, hw_set_id):
        doc = self.sets.find_one({"hwSetId": hw_set_id})
        return HardwareSet.from_dict(doc) if doc else None

    def take_from_pool(self, hw_set_id, quantity):
        """Lower availability only if enough units are on the shelf. Returns True on success."""
        result = self.sets.update_one(
            {"hwSetId": hw_set_id, "availability": {"$gte": quantity}},
            {"$inc": {"availability": -quantity}},
        )
        return result.modified_count == 1

    def return_to_pool(self, hw_set_id, quantity):
        self.sets.update_one({"hwSetId": hw_set_id}, {"$inc": {"availability": quantity}})

    # ---------- per-project checkouts ----------

    def add_to_project(self, project_id, hw_set_id, quantity):
        self.checkouts.update_one(
            {"projectId": project_id, "hwSetId": hw_set_id},
            {"$inc": {"quantity": quantity}},
            upsert=True,
        )

    def remove_from_project(self, project_id, hw_set_id, quantity):
        """Lower the project's holding only if it has enough. Returns True on success."""
        result = self.checkouts.update_one(
            {"projectId": project_id, "hwSetId": hw_set_id, "quantity": {"$gte": quantity}},
            {"$inc": {"quantity": -quantity}},
        )
        return result.modified_count == 1

    def checkouts_for_project(self, project_id):
        return [Checkout.from_dict(d) for d in self.checkouts.find({"projectId": project_id})]

    def project_holds_hardware(self, project_id):
        return self.checkouts.find_one({"projectId": project_id, "quantity": {"$gt": 0}}) is not None

    def delete_checkouts_for_project(self, project_id):
        self.checkouts.delete_many({"projectId": project_id})
