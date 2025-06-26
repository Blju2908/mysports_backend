from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
if TYPE_CHECKING:
    from .training_plan_model import TrainingPlan
    from .block_model import Block

class WorkoutStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    DONE = "done"

class Workout(SQLModel, table=True):
    __tablename__ = "workouts"

    id: Optional[int] = Field(default=None, primary_key=True)
    training_plan_id: Optional[int] = Field(default=None, foreign_key="training_plans.id")
    name: str
    date_created: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    focus: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)

    plan: Optional["TrainingPlan"] = Relationship(back_populates="workouts")
    blocks: List["Block"] = Relationship(back_populates="workout", cascade_delete=True, sa_relationship_kwargs={"order_by": "Block.position"})

    def get_sorted_blocks(self) -> List["Block"]:
        """Gibt automatisch sortierte Blocks zurück basierend auf position field"""
        return sorted(self.blocks, key=lambda b: b.position)

    @property
    def status(self) -> WorkoutStatusEnum:
        """Berechnet Status direkt am Model - keine separate Funktion nötig!"""
        sorted_blocks = self.get_sorted_blocks()
        if not sorted_blocks:
            return WorkoutStatusEnum.NOT_STARTED
        
        from .set_model import SetStatus  # Import hier um Circular Import zu vermeiden
        all_sets = [s for block in sorted_blocks for ex in block.exercises for s in ex.sets]
        
        if not all_sets:
            return WorkoutStatusEnum.NOT_STARTED
        
        done_sets = [s for s in all_sets if s.status == SetStatus.done]
        
        if len(done_sets) == len(all_sets):
            return WorkoutStatusEnum.DONE
        elif len(done_sets) > 0:
            return WorkoutStatusEnum.STARTED
        return WorkoutStatusEnum.NOT_STARTED
