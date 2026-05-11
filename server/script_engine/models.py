from pydantic import BaseModel, Field
from typing import List
from server.models import Script


class NPC(BaseModel):
    name: str
    age: int
    occupation: str
    description: str
    relationship_to_victim: str
    knows: List[str] = Field(default_factory=list)


class TimelineEntry(BaseModel):
    time: str  # "21:30" or "案发前2小时"
    event: str
    witnesses: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    from_role: str
    to_role: str
    relation: str
    tension: int = 0  # 0-10


class ScriptV2(Script):
    """Extended script model — backward compatible with Script."""
    npcs: List[NPC] = Field(default_factory=list)
    timeline: List[TimelineEntry] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    atmosphere: str = ""
    key_questions: List[str] = Field(default_factory=list)
