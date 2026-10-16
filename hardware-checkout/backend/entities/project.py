from pydantic import BaseModel, Field


class Project(BaseModel):
    """The project object stored in the projects database.

    `members` holds userIds only. Users live in a different database, so we
    reference them by id instead of embedding or joining user documents.
    """

    projectId: str = Field(..., examples=["proj-101"])
    name: str = Field(..., examples=["Sensor Array"])
    description: str = Field("", examples=["Tests with HWSet1"])
    members: list[str] = Field(default_factory=list)

    def to_dict(self):
        return {
            "projectId": self.projectId,
            "name": self.name,
            "description": self.description,
            "members": self.members,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            projectId=data["projectId"],
            name=data["name"],
            description=data.get("description", ""),
            members=data.get("members", []),
        )


class CreateProjectRequest(BaseModel):
    userId: str
    projectId: str
    name: str
    description: str = ""


class JoinProjectRequest(BaseModel):
    userId: str
    projectId: str
