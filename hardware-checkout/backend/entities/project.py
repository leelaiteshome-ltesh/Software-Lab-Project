from datetime import datetime

from pydantic import BaseModel, Field


class Project(BaseModel):
    """The project object stored in the projects database.

    `owner` is the userId that created the project. `members` holds userIds
    (owner included). Users live in a different database, so we reference
    them by id instead of embedding or joining user documents.
    """

    projectId: str = Field(..., examples=["sensor-101"])
    name: str = Field(..., examples=["Sensor Array"])
    description: str = Field("", examples=["Tests with HWSet1"])
    owner: str = Field("", examples=["asamant"])
    members: list[str] = Field(default_factory=list)
    createdAt: datetime | None = None

    def to_dict(self):
        return {
            "projectId": self.projectId,
            # Lowercase copy so IDs are unique regardless of case.
            "projectIdLower": self.projectId.lower(),
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
            # Projects made before owners existed: the first member created it.
            owner=data.get("owner") or (members[0] if members else ""),
            members=members,
            createdAt=data.get("createdAt"),
        )


class CreateProjectRequest(BaseModel):
    userId: str
    projectId: str
    name: str
    description: str = ""


class JoinProjectRequest(BaseModel):
    userId: str
    projectId: str


class UserRequest(BaseModel):
    userId: str


class MessageResponse(BaseModel):
    message: str
