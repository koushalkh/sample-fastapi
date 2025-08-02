from pydantic import BaseModel


class AbendItem(BaseModel):
    abendId: str
    name: str


class AbendDetail(BaseModel):
    abendId: str
    name: str
    severity: str
    description: str
