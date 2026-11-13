import os

from entities.hardware import ProjectHardware


class HardwareServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def default_hardware_sets():
    """The two hardware sets the system tracks. Capacities can be changed in .env."""
    return {
        "HWSet1": int(os.getenv("HWSET1_CAPACITY", "100")),
        "HWSet2": int(os.getenv("HWSET2_CAPACITY", "100")),
    }


class HardwareService:
    """Business logic for checking hardware out and in.

    Rules:
      - Only project members can check hardware out or in
      - Quantity must be a whole number >= 1
      - Can't take more than is available
      - Can't return more than the project holds
    """

    def __init__(self, dataservice, project_dataservice, default_sets=None):
        self.dataservice = dataservice
        self.projects = project_dataservice
        self.default_sets = default_hardware_sets() if default_sets is None else default_sets
        self._seeded = False

    # ---------- helpers ----------

    def _seed(self):
        """Make sure HWSet1 and HWSet2 exist. Never overwrites existing numbers."""
        if not self._seeded:
            for hw_set_id, capacity in self.default_sets.items():
                self.dataservice.ensure_set(hw_set_id, capacity)
            self._seeded = True

    def _require_member(self, user_id, project_id):
        if not user_id or not project_id:
            raise HardwareServiceError("userId and projectID are required", 400)
        project = self.projects.get_by_project_id(project_id)
        if project is None:
            raise HardwareServiceError("Project not found", 404)
        if user_id not in project.members:
            raise HardwareServiceError("Only project members can do that", 403)
        return project

    def _get_set(self, hw_set_id):
        self._seed()
        hw_set = self.dataservice.get_set(hw_set_id)
        if hw_set is None:
            raise HardwareServiceError("Hardware set not found", 404)
        return hw_set

    @staticmethod
    def _parse_quantity(quantity):
        if isinstance(quantity, bool):
            quantity = None
        elif isinstance(quantity, str):
            quantity = quantity.strip()
            quantity = int(quantity) if quantity.isdigit() else None
        elif isinstance(quantity, float):
            quantity = int(quantity) if quantity.is_integer() else None
        if not isinstance(quantity, int) or quantity < 1:
            raise HardwareServiceError("Quantity must be a whole number of at least 1", 400)
        return quantity

    # ---------- reads ----------

    def list_sets(self):
        self._seed()
        return self.dataservice.list_sets()

    def for_project(self, user_id, project_id):
        self._require_member(user_id, project_id)
        held = {c.hwSetId: c.quantity for c in self.dataservice.checkouts_for_project(project_id)}
        return [
            ProjectHardware(
                hwSetId=s.hwSetId,
                capacity=s.capacity,
                availability=s.availability,
                checkedOut=held.get(s.hwSetId, 0),
            )
            for s in self.list_sets()
        ]

    # ---------- check out / check in ----------

    def check_out(self, user_id, project_id, hw_set_id, quantity):
        self._require_member(user_id, project_id)
        quantity = self._parse_quantity(quantity)
        hw_set = self._get_set(hw_set_id)
        if quantity > hw_set.availability or not self.dataservice.take_from_pool(hw_set_id, quantity):
            current = self.dataservice.get_set(hw_set_id).availability
            raise HardwareServiceError(f"Only {current} unit(s) of {hw_set_id} available", 409)
        self.dataservice.add_to_project(project_id, hw_set_id, quantity)
        return self.for_project(user_id, project_id)

    def check_in(self, user_id, project_id, hw_set_id, quantity):
        self._require_member(user_id, project_id)
        quantity = self._parse_quantity(quantity)
        self._get_set(hw_set_id)
        if not self.dataservice.remove_from_project(project_id, hw_set_id, quantity):
            held = next(
                (c.quantity for c in self.dataservice.checkouts_for_project(project_id) if c.hwSetId == hw_set_id),
                0,
            )
            raise HardwareServiceError(f"This project only has {held} unit(s) of {hw_set_id} checked out", 409)
        self.dataservice.return_to_pool(hw_set_id, quantity)
        return self.for_project(user_id, project_id)
