from pydantic import BaseModel, Field


class HardwareSet(BaseModel):
    """A pool of identical hardware units (e.g. HWSet1).

    `availability` is how many units are on the shelf right now;
    `capacity - availability` units are checked out across all projects.
    """

    hwSetId: str = Field(..., examples=["HWSet1"])
    capacity: int = Field(..., examples=[100])
    availability: int = Field(..., examples=[100])

    def to_dict(self):
        return {"hwSetId": self.hwSetId, "capacity": self.capacity, "availability": self.availability}

    @classmethod
    def from_dict(cls, data):
        return cls(hwSetId=data["hwSetId"], capacity=data["capacity"], availability=data["availability"])


class Checkout(BaseModel):
    """How many units of one hardware set a project currently holds."""

    projectId: str
    hwSetId: str
    quantity: int

    @classmethod
    def from_dict(cls, data):
        return cls(projectId=data["projectId"], hwSetId=data["hwSetId"], quantity=data["quantity"])


class ProjectHardware(BaseModel):
    """One row of the Project page's hardware table."""

    hwSetId: str
    capacity: int
    availability: int
    checkedOut: int = Field(..., description="Units this project currently holds")


class HardwareRequest(BaseModel):
    userId: str
    projectId: str
    hwSetId: str
    # Validated in HardwareService so the error message is friendly.
    quantity: int | float | str
