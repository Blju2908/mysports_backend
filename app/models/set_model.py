from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List, Union
from enum import Enum
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from .exercise_model import Exercise

class SetStatus(str, Enum):
    open = "open"
    done = "done"

class SetTag(str, Enum):
    warm_up = "warm_up"

class Set(SQLModel, table=True):
    __tablename__ = "sets"
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: Optional[str] = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)
    exercise_id: int = Field(foreign_key="exercises.id", ondelete="CASCADE")
    
    # Planned values
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None
    
    # Common values
    rest_time: Optional[int] = None  # in seconds

    # Ordering
    position: Optional[int] = Field(default=0, description="Position for stable sorting of sets within an exercise")
    
    # Status tracking
    status: SetStatus = Field(default=SetStatus.open)
    completed_at: Optional[datetime] = None
    
    # Tag for set type (e.g., warm_up)
    tag: Optional[SetTag] = None
    
    exercise: "Exercise" = Relationship(back_populates="sets")

    @classmethod
    def from_values_list(cls, values: List[Optional[Union[float, int, str]]]) -> Optional["Set"]:
        """
        Creates a Set instance from the LLM output values array.
        Values format: [weight, reps, duration, distance, rest_time, tag]
        
        Args:
            values: List of values in the order [weight, reps, duration, distance, rest_time, tag]
        
        Returns:
            Set instance or None if all values are None/empty
        """
        if not values or len(values) == 0:
            return None
        
        # Ensure we have at least 6 values, pad with None if needed
        padded_values = values + [None] * (6 - len(values))
        
        weight = padded_values[0] if padded_values[0] is not None else None
        reps = padded_values[1] if padded_values[1] is not None else None
        duration = padded_values[2] if padded_values[2] is not None else None
        distance = padded_values[3] if padded_values[3] is not None else None
        rest_time = padded_values[4] if padded_values[4] is not None else None
        tag_str = padded_values[5] if padded_values[5] is not None else None
        
        # Convert to proper types
        try:
            if weight is not None:
                weight = float(weight)
            if reps is not None:
                reps = int(reps)
            if duration is not None:
                duration = int(duration)
            if distance is not None:
                distance = float(distance)
            if rest_time is not None:
                rest_time = int(rest_time)
            
            # Convert tag string to enum
            tag = None
            if tag_str:
                try:
                    tag = SetTag(tag_str)
                except ValueError:
                    print(f"Warning: Invalid tag value: {tag_str}")
                    tag = None
        except (ValueError, TypeError):
            print(f"Warning: Could not convert values to proper types: {values}")
            return None
        
        # Check if at least one value is not None and not zero
        if not any([
            weight and weight > 0,
            reps and reps > 0, 
            duration and duration > 0,
            distance and distance > 0,
            rest_time and rest_time > 0
        ]):
            return None
        
        return cls(
            weight=weight,
            reps=reps,
            duration=duration,
            distance=distance,
            rest_time=rest_time,
            status=SetStatus.open,
            tag=tag
        )
