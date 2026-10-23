"""In-memory stand-ins for the MongoDB dataservices so tests run offline."""

from entities.hardware import DEFAULT_HARDWARE_SETS


class FakeUserDataService:
    def __init__(self, user_ids=()):
        self.user_ids = set(user_ids)

    def get_by_user_id(self, user_id):
        return user_id if user_id in self.user_ids else None


class FakeProjectDataService:
    def __init__(self):
        self.projects = {}  # keyed by lowercase projectId, like the real index

    def create(self, project):
        key = project.projectId.lower()
        if key in self.projects:
            return None
        self.projects[key] = project
        return project

    def get_by_project_id(self, project_id):
        p = self.projects.get(project_id.lower())
        return p.model_copy(deep=True) if p else None

    def add_member(self, project_id, user_id):
        p = self.projects[project_id.lower()]
        if user_id not in p.members:
            p.members.append(user_id)

    def remove_member(self, project_id, user_id):
        p = self.projects[project_id.lower()]
        p.members = [m for m in p.members if m != user_id]

    def delete(self, project_id):
        return self.projects.pop(project_id.lower(), None) is not None

    def list_for_user(self, user_id):
        return [p for p in self.projects.values() if user_id in p.members]


class FakeHardwareDataService:
    def __init__(self, sets=DEFAULT_HARDWARE_SETS):
        self.sets = {s.hwSetId: s.model_copy() for s in sets}
        self.checkouts = {}  # (projectId, hwSetId) -> quantity

    def list_sets(self):
        return [self.sets[k].model_copy() for k in sorted(self.sets)]

    def get_set(self, hw_set_id):
        s = self.sets.get(hw_set_id)
        return s.model_copy() if s else None

    def reserve(self, hw_set_id, quantity):
        s = self.sets[hw_set_id]
        if s.availability < quantity:
            return None
        s.availability -= quantity
        return s.model_copy()

    def release(self, hw_set_id, quantity):
        s = self.sets[hw_set_id]
        if s.availability + quantity > s.capacity:
            return None
        s.availability += quantity
        return s.model_copy()

    def add_to_project(self, project_id, hw_set_id, quantity):
        key = (project_id, hw_set_id)
        self.checkouts[key] = self.checkouts.get(key, 0) + quantity
        return self.checkouts[key]

    def take_from_project(self, project_id, hw_set_id, quantity):
        key = (project_id, hw_set_id)
        if self.checkouts.get(key, 0) < quantity:
            return None
        self.checkouts[key] -= quantity
        left = self.checkouts[key]
        if left == 0:
            del self.checkouts[key]
        return left

    def get_project_quantity(self, project_id, hw_set_id):
        return self.checkouts.get((project_id, hw_set_id), 0)

    def get_project_checkouts(self, project_id):
        from entities.hardware import ProjectHardware

        return [
            ProjectHardware(hwSetId=h, quantity=q)
            for (p, h), q in self.checkouts.items()
            if p == project_id and q > 0
        ]
