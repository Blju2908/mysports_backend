from enum import Enum

class ExerciseType(str, Enum):
    repetitions = "repetitions"
    duration = "duration"

class BlockStatus(str, Enum):
    incomplete = "incomplete"
    in_progress = "in_progress"
    complete = "complete"

class WorkoutStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    aborted = "aborted" 