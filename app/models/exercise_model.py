from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List

if TYPE_CHECKING:
    from .set_model import Set
    from .block_model import Block

class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    notes: Optional[str] = Field(default=None)
    superset_id: Optional[str] = Field(default=None, description="Eindeutige ID für Supersets. Übungen mit derselben superset_id werden abwechselnd ausgeführt.")
    block_id: int = Field(foreign_key="blocks.id", ondelete="CASCADE")
    
    block: "Block" = Relationship(back_populates="exercises")
    sets: List["Set"] = Relationship(back_populates="exercise", cascade_delete=True)
    
