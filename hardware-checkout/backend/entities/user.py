from pydantic import BaseModel, Field


class User(BaseModel):
    """The user object stored in MongoDB. Password is always the encrypted value."""

    userId: str = Field(..., examples=["asamant"])
    password: str = Field(..., examples=["Temp123"])

    def to_dict(self):
        return {"userId": self.userId, "password": self.password}

    @classmethod
    def from_dict(cls, data):
        return cls(userId=data["userId"], password=data["password"])


class UserResponse(BaseModel):
    """What the API sends back. Never includes the password."""

    userId: str
    message: str
