"""In-memory stand-ins for the MongoDB dataservices so tests run offline."""

from entities.hardware import Checkout, HardwareSet
from entities.user import User


class FakeUserDataService:
    def __init__(self, user_ids=()):
        self.users = {u: User(userId=u, password="x") for u in user_ids}

    def create(self, user):
        self.users[user.userId] = user
        return user

    def get_by_user_id(self, user_id):
        return self.users.get(user_id)


class FakeProjectDataService:
    def __init__(self):
        self.projects = {}

    def create(self, project):
        self.projects[project.projectId] = project
        return project

    def get_by_project_id(self, project_id):
        return self.projects.get(project_id)

    def add_member(self, project_id, user_id):
        p = self.projects[project_id]
        if user_id not in p.members:
            p.members.append(user_id)

    def remove_member(self, project_id, user_id):
        p = self.projects[project_id]
        p.members = [m for m in p.members if m != user_id]

    def delete(self, project_id):
        return self.projects.pop(project_id, None) is not None

    def list_for_user(self, user_id):
        return [p for p in self.projects.values() if user_id in p.members]


class FakeHardwareDataService:
    def __init__(self):
        self.sets = {}
        self.checkouts = {}  # (projectId, hwSetId) -> quantity

    def ensure_set(self, hw_set_id, capacity):
        self.sets.setdefault(hw_set_id, HardwareSet(hwSetId=hw_set_id, capacity=capacity, availability=capacity))

    def list_sets(self):
        return [self.sets[k] for k in sorted(self.sets)]

    def get_set(self, hw_set_id):
        return self.sets.get(hw_set_id)

    def take_from_pool(self, hw_set_id, quantity):
        s = self.sets[hw_set_id]
        if s.availability < quantity:
            return False
        s.availability -= quantity
        return True

    def return_to_pool(self, hw_set_id, quantity):
        self.sets[hw_set_id].availability += quantity

    def add_to_project(self, project_id, hw_set_id, quantity):
        key = (project_id, hw_set_id)
        self.checkouts[key] = self.checkouts.get(key, 0) + quantity

    def remove_from_project(self, project_id, hw_set_id, quantity):
        key = (project_id, hw_set_id)
        if self.checkouts.get(key, 0) < quantity:
            return False
        self.checkouts[key] -= quantity
        return True

    def checkouts_for_project(self, project_id):
        return [Checkout(projectId=p, hwSetId=h, quantity=q) for (p, h), q in self.checkouts.items() if p == project_id]

    def project_holds_hardware(self, project_id):
        return any(q > 0 for (p, _), q in self.checkouts.items() if p == project_id)

    def delete_checkouts_for_project(self, project_id):
        self.checkouts = {k: v for k, v in self.checkouts.items() if k[0] != project_id}
