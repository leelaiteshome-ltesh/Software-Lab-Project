from pydantic import BaseModel, Field


class HardwareSet(BaseModel):
    """A pool of identical hardware units, stored in the hardware database."""

    hwSetId: str = Field(..., examples=["HWSet1"])
    name: str = Field(..., examples=["Hardware Set 1"])
    capacity: int = Field(..., examples=[100])
    availability: int = Field(..., examples=[100])

    def to_dict(self):
        return self.model_dump()

    @classmethod
    def from_dict(cls, data):
        return cls(
            hwSetId=data["hwSetId"],
            name=data["name"],
            capacity=data["capacity"],
            availability=data["availability"],
        )


class ProjectHardware(BaseModel):
    """How many units of one hardware set a project currently has checked out."""

    hwSetId: str
    quantity: int


class HardwareRequest(BaseModel):
    userId: str
    projectId: str
    hwSetId: str = Field(..., examples=["HWSet1"])
    quantity: int = Field(..., examples=[5])


class HardwareResult(BaseModel):
    hardwareSet: HardwareSet
    projectQuantity: int
    message: str


# Created on startup if they don't exist yet.
DEFAULT_HARDWARE_SETS = [
    HardwareSet(hwSetId="HWSet1", name="Hardware Set 1", capacity=100, availability=100),
    HardwareSet(hwSetId="HWSet2", name="Hardware Set 2", capacity=100, availability=100),
]
