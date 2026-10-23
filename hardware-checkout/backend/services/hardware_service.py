from entities.hardware import HardwareResult


class HardwareServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class HardwareService:
    """Business logic for checking hardware in and out of projects.

    Hardware is checked out to a project, and any member of that project can
    check it in or out.
    """

    def __init__(self, hardware_dataservice, project_dataservice):
        self.hardware = hardware_dataservice
        self.projects = project_dataservice

    def _member_project(self, user_id, project_id):
        if not user_id or not (project_id or "").strip():
            raise HardwareServiceError("userId and projectID are required", 400)
        project = self.projects.get_by_project_id(project_id.strip())
        if project is None:
            raise HardwareServiceError("Project not found", 404)
        if user_id not in project.members:
            raise HardwareServiceError("You're not a member of this project", 403)
        return project

    def _validate(self, user_id, project_id, hw_set_id, quantity):
        # bool is a subclass of int, so rule it out explicitly.
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
            raise HardwareServiceError("Quantity must be a whole number of at least 1", 400)
        project = self._member_project(user_id, project_id)
        hw_set = self.hardware.get_set(hw_set_id)
        if hw_set is None:
            raise HardwareServiceError("Hardware set not found", 404)
        return project, hw_set

    def list_sets(self):
        return self.hardware.list_sets()

    def project_hardware(self, user_id, project_id):
        project = self._member_project(user_id, project_id)
        return self.hardware.get_project_checkouts(project.projectId)

    def check_out(self, user_id, project_id, hw_set_id, quantity):
        project, hw_set = self._validate(user_id, project_id, hw_set_id, quantity)
        updated = self.hardware.reserve(hw_set.hwSetId, quantity)
        if updated is None:
            available = self.hardware.get_set(hw_set.hwSetId).availability
            raise HardwareServiceError(f"Only {available} unit(s) of {hw_set.hwSetId} available", 400)
        project_qty = self.hardware.add_to_project(project.projectId, hw_set.hwSetId, quantity)
        return HardwareResult(
            hardwareSet=updated,
            projectQuantity=project_qty,
            message=f"Checked out {quantity} unit(s) of {hw_set.hwSetId}",
        )

    def check_in(self, user_id, project_id, hw_set_id, quantity):
        project, hw_set = self._validate(user_id, project_id, hw_set_id, quantity)
        project_qty = self.hardware.take_from_project(project.projectId, hw_set.hwSetId, quantity)
        if project_qty is None:
            has = self.hardware.get_project_quantity(project.projectId, hw_set.hwSetId)
            raise HardwareServiceError(
                f"This project only has {has} unit(s) of {hw_set.hwSetId} checked out", 400
            )
        updated = self.hardware.release(hw_set.hwSetId, quantity)
        if updated is None:  # shouldn't happen unless the two collections drifted apart
            raise HardwareServiceError("Hardware set counts are out of sync", 500)
        return HardwareResult(
            hardwareSet=updated,
            projectQuantity=project_qty,
            message=f"Checked in {quantity} unit(s) of {hw_set.hwSetId}",
        )
