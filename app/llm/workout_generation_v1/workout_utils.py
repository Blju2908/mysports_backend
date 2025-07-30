from typing import List, Optional
from datetime import datetime
import json
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set


def format_training_history_for_llm(
    training_history_workouts: List[Workout],
) -> str | None:
    """
    Formats the training history into a structured JSON string suitable for the LLM.
    Focuses on when the user trained, their notes, and actual executed exercises.
    Only includes workouts that have at least one completed set.
    Optimized for information density: removes null/zero values, compresses identical sets, removes rest times.
    Returns None if no workouts are provided.
    """
    if not training_history_workouts:
        return None
    
    # Note: The workout history is already filtered by get_user_workout_history
    # to only include completed sets and their parent elements
    
    history_data = []
    
    for workout in training_history_workouts:
        # Find the earliest completed_at from sets as the workout completion date
        workout_completion_date_str = "N/A"
        earliest_completed_at = None
        
        for block in workout.blocks:
            for exercise in block.exercises:
                for s_set in exercise.sets:
                    if s_set.completed_at:
                        if earliest_completed_at is None or s_set.completed_at < earliest_completed_at:
                            earliest_completed_at = s_set.completed_at
                            
        if earliest_completed_at:
            workout_completion_date_str = earliest_completed_at.strftime("%Y-%m-%d")

        # Create workout object
        workout_obj = {
            "name": workout.name if workout.name else "Unnamed Workout",
            "date": workout_completion_date_str,
            "blocks": []
        }
        
        if workout.focus:
            workout_obj["focus"] = workout.focus
        if workout.duration:
            workout_obj["duration"] = workout.duration
        if workout.notes:
            workout_obj["notes"] = workout.notes
        
        # Add blocks
        for block in workout.blocks:
            block_obj = {
                "name": block.name if block.name else "Unnamed Block",
                "exercises": []
            }
            
            if block.notes:
                block_obj["notes"] = block.notes
            
            # Add exercises
            for exercise in block.exercises:
                exercise_obj = {
                    "name": exercise.name if exercise.name else "Unnamed Exercise",
                    "sets": []
                }
                
                if exercise.notes:
                    exercise_obj["notes"] = exercise.notes
                if exercise.superset_id:
                    exercise_obj["superset_id"] = exercise.superset_id
                
                # Collect and compress sets
                raw_sets = []
                for s in exercise.sets:
                    set_obj = {}
                    if s.weight is not None and s.weight != 0.0:
                        set_obj["weight"] = s.weight
                    if s.reps is not None and s.reps != 0:
                        set_obj["reps"] = s.reps
                    if s.duration is not None and s.duration != 0:
                        set_obj["duration"] = s.duration
                    if s.distance is not None and s.distance != 0.0:
                        set_obj["distance"] = s.distance
                    # Note: rest_time completely removed as requested
                    
                    if set_obj:  # Only add if there's at least one non-zero value
                        raw_sets.append(set_obj)
                
                # Compress identical sets (simple approach)
                if raw_sets:
                    compressed_sets = []
                    current_set = raw_sets[0]
                    count = 1
                    
                    for i in range(1, len(raw_sets)):
                        if raw_sets[i] == current_set:
                            count += 1
                        else:
                            # Add the compressed set
                            if count == 1:
                                compressed_sets.append(current_set)
                            else:
                                compressed_set = current_set.copy()
                                compressed_set["count"] = count
                                compressed_sets.append(compressed_set)
                            
                            # Start new group
                            current_set = raw_sets[i]
                            count = 1
                    
                    # Add the last group
                    if count == 1:
                        compressed_sets.append(current_set)
                    else:
                        compressed_set = current_set.copy()
                        compressed_set["count"] = count
                        compressed_sets.append(compressed_set)
                    
                    exercise_obj["sets"] = compressed_sets
                
                if exercise_obj.get("sets"):  # Only add if there's at least one set
                    block_obj["exercises"].append(exercise_obj)
            
            if block_obj["exercises"]:  # Only add if there's at least one exercise
                workout_obj["blocks"].append(block_obj)
        
        if workout_obj["blocks"]:  # Only add if there's at least one block
            history_data.append(workout_obj)

    if not history_data:
        return None

    # Convert to JSON string
    return json.dumps(history_data, ensure_ascii=False)


def summarize_training_history(
    training_history_workouts: List[Workout],
) -> Optional[str]:
    """
    Summarizes training history into a token-efficient, structured text format
    based on the user's final requested format.
    """
    if not training_history_workouts:
        return None

    summary_lines = [
        "--- WORKOUT HISTORY SUMMARY ---",
        "*Legende: r (Wiederholungen) | kg (Gewicht) | m (Distanz) | s (Dauer) | p (Pause)*\n"
    ]

    for workout in training_history_workouts:
        date_str = "N/A"
        earliest_completed_at = None
        for block in workout.blocks:
            for exercise in block.exercises:
                for s_set in exercise.sets:
                    if s_set.completed_at:
                        if earliest_completed_at is None or s_set.completed_at < earliest_completed_at:
                            earliest_completed_at = s_set.completed_at
        
        final_date = earliest_completed_at or workout.date_created
        if final_date:
            date_str = final_date.strftime("%Y-%m-%d")

        header_parts = [f"**Workout: {workout.name or 'Unbenanntes Workout'}", date_str]
        if workout.focus:
            header_parts.append(f"Fokus: {workout.focus}**")
        else:
            header_parts[-1] += "**"
        
        summary_lines.append(" | ".join(header_parts))
        
        if workout.description:
            summary_lines.append(f"*Beschreibung: {workout.description}*")
        if workout.notes:
            summary_lines.append(f"*Notizen: {workout.notes}*")
        
        for block in sorted(workout.blocks, key=lambda b: b.position):
            summary_lines.append(f"\n  **Block: {block.name or 'Unbenannter Block'}**")
            if block.notes:
                summary_lines.append(f"    *Notiz: {block.notes}*")

            for exercise in sorted(block.exercises, key=lambda e: e.position):
                summary_lines.append(f"    - {exercise.name or 'Unbenannte Übung'}")
                if exercise.notes:
                    summary_lines.append(f"      - Notiz: \"{exercise.notes}\"")
                
                for s_set in sorted(exercise.sets, key=lambda s: s.position):
                    set_parts = []
                    if s_set.reps: set_parts.append(f"{s_set.reps}r")
                    if s_set.weight: set_parts.append(f"{s_set.weight}kg")
                    if s_set.distance: set_parts.append(f"{s_set.distance}m")
                    if s_set.duration: set_parts.append(f"{s_set.duration}s")
                    if s_set.rest_time: set_parts.append(f"p: {s_set.rest_time}s")
                    
                    if set_parts:
                        summary_lines.append(f"      - {' / '.join(set_parts)}")

        summary_lines.append("")

    summary_lines.append("--- END OF HISTORY ---")
    
    return "\n".join(summary_lines) 