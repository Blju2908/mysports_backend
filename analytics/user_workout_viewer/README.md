# User Workout Viewer

A comprehensive toolset for viewing and analyzing workouts for specific users in the MySports application.

## Overview

This toolset provides multiple ways to view and analyze user workouts:

1. **Main Script** (`user_workout_viewer.py`) - Fetches and formats user workouts, exports to JSON
2. **HTML Viewer** (`user_workout_viewer.html`) - Visual browser-based workout viewer with filtering
3. **Console Viewer** (`console_viewer.py`) - Simple command-line tool for quick viewing

## Features

- **User-specific workout viewing** - View all workouts for a specific user
- **Completion tracking** - See workout and set completion status
- **Statistics and insights** - Overall completion rates and progress
- **Multiple output formats** - Console, HTML, and JSON export
- **Filtering capabilities** - Filter by status, focus, date range
- **Superset visualization** - Clear display of superset relationships
- **Execution data** - Show planned vs. actual execution values

## Setup

### 1. Configure User ID

In each script, set the `USER_ID` variable to the UUID of the user you want to view:

```python
USER_ID = "your-user-uuid-here"  # Replace with actual UUID
```

### 2. Environment Setup

The scripts automatically load environment variables from `.env.production` in the backend directory.

## Usage

### Option 1: Main Script (Recommended)

```bash
cd backend/analytics/user_workout_viewer
python user_workout_viewer.py
```

**What it does:**
- Fetches all workouts for the specified user
- Displays comprehensive statistics
- Shows detailed workout summaries in console
- Exports formatted data to JSON for HTML viewer

**Output:**
- Console output with statistics and summaries
- JSON file: `output/user_workouts.json`

### Option 2: HTML Viewer

1. Run the main script to generate JSON data
2. Open `user_workout_viewer.html` in a web browser
3. Load the generated JSON file

**Features:**
- Interactive filtering by status, focus, date
- Visual progress bars and completion indicators
- Responsive design for mobile/desktop
- Detailed exercise and set information

### Option 3: Console Viewer

```bash
cd backend/analytics/user_workout_viewer
python console_viewer.py
```

**Features:**
- Quick command-line viewing
- Interactive prompts for detailed viewing
- Simple statistics and summaries
- No browser required

## File Structure

```
backend/analytics/user_workout_viewer/
├── user_workout_viewer.py      # Main script with JSON export
├── user_workout_viewer.html    # Enhanced HTML viewer
├── console_viewer.py           # Simple console viewer
├── README.md                   # This file
└── output/                     # Generated files
    └── user_workouts.json      # Exported workout data
```

## Data Structure

The scripts work with the following database models:

- **Workout** - Main workout container with metadata
- **Block** - Groups of exercises within a workout
- **Exercise** - Individual exercises with sets
- **Set** - Individual sets with execution data

### Key Information Displayed

**Workout Level:**
- Name, description, duration, focus
- Creation date and status
- Muscle groups targeted
- Overall completion percentage

**Block Level:**
- Block name and description
- Exercise count and types (single/superset)
- Block-specific notes

**Exercise Level:**
- Exercise name and description
- Superset relationships
- Set count and completion status
- Execution values (weight, reps, duration, etc.)

**Set Level:**
- Set number and status (open/done)
- Planned vs. actual values
- Completion timestamp

## Troubleshooting

### Common Issues

1. **Invalid UUID Error**
   - Ensure the USER_ID is a valid UUID format
   - Check that the user exists in the database

2. **Database Connection Error**
   - Verify `.env.production` file exists
   - Check database credentials and connectivity

3. **No Workouts Found**
   - Confirm the user has created workouts
   - Check if using the correct user ID

4. **Import Errors**
   - Ensure you're running from the correct directory
   - Verify all required dependencies are installed

### Debug Mode

Add debug prints to see more information:

```python
# In user_workout_viewer.py
print(f"Debug: Found {len(workouts)} workouts")
for workout in workouts:
    print(f"Debug: Workout {workout.id} - {workout.name}")
```

## Examples

### View Recent Workouts Only

```python
# In user_workout_viewer.py
LIMIT = 10  # Only show last 10 workouts
```

### Filter by Status

```python
# In console_viewer.py
# Add filtering logic to show only completed workouts
workouts = [w for w in workouts if w.status == WorkoutStatusEnum.DONE]
```

### Custom Statistics

```python
# Add custom analysis
def analyze_workout_trends(workouts):
    # Your custom analysis here
    pass
```

## Integration with Existing Tools

This viewer integrates with the existing analytics infrastructure:

- Uses the same database connection utilities
- Follows the same environment setup pattern
- Compatible with existing workout data structures
- Can be extended for additional analytics

## Future Enhancements

Potential improvements:

1. **Trend Analysis** - Track progress over time
2. **Performance Metrics** - Weight progression, volume tracking
3. **Export Options** - PDF reports, CSV data
4. **Real-time Updates** - Live workout tracking
5. **Comparative Analysis** - Compare multiple users or time periods 