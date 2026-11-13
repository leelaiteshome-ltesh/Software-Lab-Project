from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    """The project object stored in the projects database.

    `owner` and `members` hold userIds only. Users live in a different
    database, so we reference them by id instead of embedding or joining
    user documents. The owner is always also the first member.
    """

    projectId: str = Field(..., examples=["proj-101"])
    name: str = Field(..., examples=["Sensor Array"])
    description: str = Field("", examples=["Tests with HWSet1"])
    owner: str = Field("", examples=["asamant"])
    members: list[str] = Field(default_factory=list)
    createdAt: Optional[datetime] = None

    def to_dict(self):
        return {
            "projectId": self.projectId,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "members": self.members,
            "createdAt": self.createdAt,
        }

    @classmethod
    def from_dict(cls, data):
        members = data.get("members", [])
        return cls(
            projectId=data["projectId"],
            name=data["name"],
            description=data.get("description", ""),
            # Projects created before `owner` existed: treat the first member as owner.
            owner=data.get("owner") or (members[0] if members else ""),
            members=members,
            createdAt=data.get("createdAt"),
        )

    @staticmethod
    def now():
        return datetime.now(timezone.utc)


class CreateProjectRequest(BaseModel):
    userId: str
    projectId: str
    name: str
    description: str = ""


class JoinProjectRequest(BaseModel):
    userId: str
    projectId: str


class LeaveProjectRequest(BaseModel):
    userId: str
