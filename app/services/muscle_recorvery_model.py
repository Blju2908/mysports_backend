from typing import Optional, List, TYPE_CHECKING, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from enum import Enum
from uuid import UUID
import json # Added for JSON loading

if TYPE_CHECKING:
    from .training_plan_model import TrainingPlan
    from .block_model import Block
    from .user_model import UserModel

class MuscleRecoveryModel:

    MAX_FATIGUE = 5000.0
    RECOVERY_FACTOR = 0.6

    def __init__(self):
        self.muscle_groups = {
            "glutes": 0.0,
            "hamstrings": 0.0,
            "quadriceps": 0.0,
            "lower_back": 0.0,
            "triceps": 0.0,
            "chest": 0.0,
            "biceps": 0.0,
            "shoulders": 0.0,
            "abdominals": 0.0,
            "back": 0.0,
            "calves": 0.0,
            "trapezius": 0.0,
            "abductors": 0.0,
            "adductors": 0.0,
            "forearms": 0.0,
            "neck": 0.0
        }

    def load_exercises_from_json(self, file_path: str):
        """
        Loads exercise data from a JSON file for local development and testing.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.exercises_data = json.load(f)
            print(f"Successfully loaded {len(self.exercises_data)} exercises from {file_path}")
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            self.exercises_data = []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {file_path}")
            self.exercises_data = []
        except Exception as e:
            print(f"An unexpected error occurred while loading data: {e}")
            self.exercises_data = []

    def calculate_fatigue_level(self, activities: list):
        pass
        
        

