from pymongo import ReturnDocument

from entities.hardware import HardwareSet, ProjectHardware


class HardwareDataService:
    """CRUD for the hardware database.

    - `hardware_sets`: one document per set (capacity, availability)
    - `checkouts`: one document per (projectId, hwSetId) with the quantity out

    Updates are single atomic operations with a guard in the filter, so two
    users can't both take the last units.
    """

    def __init__(self, database):
        self.sets = database["hardware_sets"]
        self.checkouts = database["checkouts"]

    def ensure_defaults(self, default_sets):
        """Run once on startup. Creates missing sets; never resets existing ones."""
        self.sets.create_index("hwSetId", unique=True)
        self.checkouts.create_index([("projectId", 1), ("hwSetId", 1)], unique=True)
        for hw in default_sets:
            self.sets.update_one(
                {"hwSetId": hw.hwSetId}, {"$setOnInsert": hw.to_dict()}, upsert=True
            )

    def list_sets(self):
        return [HardwareSet.from_dict(d) for d in self.sets.find().sort("hwSetId", 1)]

    def get_set(self, hw_set_id):
        doc = self.sets.find_one({"hwSetId": hw_set_id})
        return HardwareSet.from_dict(doc) if doc else None

    def reserve(self, hw_set_id, quantity):
        """Lower availability if at least `quantity` is left. Returns the updated set or None."""
        doc = self.sets.find_one_and_update(
            {"hwSetId": hw_set_id, "availability": {"$gte": quantity}},
            {"$inc": {"availability": -quantity}},
            return_document=ReturnDocument.AFTER,
        )
        return HardwareSet.from_dict(doc) if doc else None

    def release(self, hw_set_id, quantity):
        """Raise availability, never above capacity. Returns the updated set or None."""
        doc = self.sets.find_one_and_update(
            {
                "hwSetId": hw_set_id,
                "$expr": {"$lte": [{"$add": ["$availability", quantity]}, "$capacity"]},
            },
            {"$inc": {"availability": quantity}},
            return_document=ReturnDocument.AFTER,
        )
        return HardwareSet.from_dict(doc) if doc else None

    def add_to_project(self, project_id, hw_set_id, quantity):
        doc = self.checkouts.find_one_and_update(
            {"projectId": project_id, "hwSetId": hw_set_id},
            {"$inc": {"quantity": quantity}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return doc["quantity"]

    def take_from_project(self, project_id, hw_set_id, quantity):
        """Lower the project's quantity if it has enough. Returns the new quantity or None."""
        doc = self.checkouts.find_one_and_update(
            {"projectId": project_id, "hwSetId": hw_set_id, "quantity": {"$gte": quantity}},
            {"$inc": {"quantity": -quantity}},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            return None
        if doc["quantity"] == 0:
            self.checkouts.delete_one({"_id": doc["_id"], "quantity": 0})
        return doc["quantity"]

    def get_project_quantity(self, project_id, hw_set_id):
        doc = self.checkouts.find_one({"projectId": project_id, "hwSetId": hw_set_id})
        return doc["quantity"] if doc else 0

    def get_project_checkouts(self, project_id):
        return [
            ProjectHardware(hwSetId=d["hwSetId"], quantity=d["quantity"])
            for d in self.checkouts.find({"projectId": project_id, "quantity": {"$gt": 0}})
        ]
