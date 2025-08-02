from pydantic import BaseModel


class SOPItem(BaseModel):
    id: str
    name: str
    description: str


class SOPDetail(BaseModel):
    id: str
    name: str
    description: str
    version: str
    content: str
    last_updated: str
