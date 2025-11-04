# PathSolver User Action Logging System

This document describes the comprehensive user action logging system implemented for evaluating how users interact with the PathSolver application.

## Overview

The logging system captures all user interactions with the application, including:
- Participant identification
- Algorithm execution steps
- Graph manipulations
- Prediction game interactions
- Solution quiz submissions
- Settings changes
- Session metadata

All logs are stored in JSONL (JSON Lines) format for easy analysis.

## Participant ID Entry

When users first access the application, they are required to enter a **Participant ID** before they can use any features. This ensures that all actions can be properly attributed to specific participants in your evaluation study.

### Key Features:
- **Mandatory Entry**: Users cannot bypass the participant ID screen
- **Flexible Format**: Accepts any alphanumeric ID (e.g., P001, USER123, etc.)
- **Persistent Tracking**: The participant ID is included in every log event
- **Session Binding**: Each participant ID is bound to a session

## Log Files

### Location
All log files are stored in the `evaluation_logs/` directory.

### File Naming Convention
```
user_actions_YYYYMMDD_HHMMSS_<session_id>.jsonl
```

Example: `user_actions_20250104_143022_a1b2c3d4.jsonl`

### Format
Each line in the log file is a JSON object with the following structure:
```json
{
  "timestamp": "2025-01-04T14:30:22.123456",
  "session_id": "a1b2c3d4",
  "participant_id": "P001",
  "task_mode_active": true,
  "current_task_number": 1,
  "current_task_description": "Find shortest path in simple graph",
  "event_type": "algorithm_step",
  "data": {
    "step_number": 1,
    "step_name": "visit_neighbors",
    "current_node": "5",
    "nodes_visited": ["1", "5"]
  }
}
```

**Fields:**
- `timestamp`: ISO 8601 formatted timestamp
- `session_id`: Unique session identifier (8-character UUID)
- `participant_id`: User-entered participant identifier
- `task_mode_active`: Whether task mode is active (true/false)
- `current_task_number`: Current task number (null if not in task mode)
- `current_task_description`: Description of current task (null if not in task mode)
- `event_type`: Type of action/event
- `data`: Event-specific data

## Event Types

### Session Events
- `session_start` - When a user starts a session
- `session_end` - When a user ends a session

### Algorithm Events
- `algorithm_start` - When the algorithm begins
- `algorithm_step` - Each step of the algorithm
- `algorithm_back_step` - When user goes back a step
- `algorithm_reset` - When algorithm is reset
- `algorithm_complete` - When algorithm finishes

### Graph Interaction Events
- `graph_selected` - When a graph type is selected
- `graph_uploaded` - When a custom graph is uploaded
- `node_added` - When a node is added to the graph
- `node_deleted` - When a node is deleted
- `edge_added` - When an edge is added
- `edge_deleted` - When an edge is deleted
- `edge_weight_updated` - When edge weight is modified
- `start_node_set` - When start node is selected
- `target_node_set` - When target node is selected

### Game/Quiz Events
- `game_toggled` - When prediction game is enabled/disabled
- `difficulty_changed` - When game difficulty changes
- `prediction_made` - When user makes a prediction
- `game_stats` - Game statistics snapshot
- `solution_quiz_toggled` - When solution quiz is enabled/disabled
- `quiz_submitted` - When user submits a quiz answer

### Task Mode Events
- `task_mode_toggled` - When task mode is enabled/disabled
- `task_started` - When a task begins
- `task_completed` - When a task is completed

### Settings Events
- `language_changed` - When UI language is changed
- `visualization_mode_changed` - When visualization mode changes
- `font_size_changed` - When font size is adjusted
- `settings_unlocked` - When admin settings are unlocked

### Error Events
- `error_occurred` - When an error occurs
- `validation_failure` - When validation fails

## Analysis Tools

### Command-Line Analysis Script

The `analyze_logs.py` script provides comprehensive log analysis:

```bash
# View full report
python analyze_logs.py evaluation_logs/user_actions_20250104_143022_a1b2c3d4.jsonl

# Export to CSV for further analysis
python analyze_logs.py evaluation_logs/user_actions_20250104_143022_a1b2c3d4.jsonl --export-csv output.csv

# Get session summary as JSON
python analyze_logs.py evaluation_logs/user_actions_20250104_143022_a1b2c3d4.jsonl --summary-only
```

### Analysis Metrics

The analysis script provides:

**Session Summary:**
- Session duration
- Total events
- Event type breakdown

**Algorithm Usage:**
- Number of algorithm runs
- Completion rate
- Average steps per run
- Back steps count
- Graph types used

**Graph Interactions:**
- Total modifications
- Nodes/edges added/deleted
- Edge weight updates
- Custom graph usage

**Game Performance:**
- Total predictions
- Accuracy
- Max score and streak

**Quiz Performance:**
- Total submissions
- Accuracy

**Task Mode Progression:**
- Tasks encountered and completed
- Completion rate
- Time spent on each task
- Task-specific performance

**Settings Changes:**
- Language changes
- Font size adjustments
- Difficulty changes

## Data Analysis with Python

You can also analyze logs programmatically:

```python
import json
from pathlib import Path

# Load a log file
log_file = Path("evaluation_logs/user_actions_20250104_143022_a1b2c3d4.jsonl")
events = []

with open(log_file, 'r') as f:
    for line in f:
        events.append(json.loads(line))

# Example: Count predictions
predictions = [e for e in events if e['event_type'] == 'prediction_made']
correct = sum(1 for p in predictions if p['data']['is_correct'])
accuracy = correct / len(predictions) if predictions else 0

print(f"Prediction accuracy: {accuracy:.1%}")
```

## Data Analysis with pandas

Export to CSV and analyze with pandas:

```python
import pandas as pd

# Load CSV export
df = pd.read_csv('output.csv')

# Filter by participant
participant_data = df[df['participant_id'] == 'P001']

# Filter by event type
algo_steps = df[df['event_type'] == 'algorithm_step']

# Compare participants
participant_summary = df.groupby('participant_id').agg({
    'event_type': 'count',
    'timestamp': ['min', 'max']
})

# Analyze prediction accuracy by participant
predictions = df[df['event_type'] == 'prediction_made']
accuracy_by_participant = predictions.groupby('participant_id')['data_is_correct'].mean()

# Filter by task number
task_1_events = df[df['current_task_number'] == 1]

# Compare performance across tasks
task_completion = df[df['event_type'] == 'task_completed'].groupby('data_task_index').size()

# Analyze time spent per task per participant
task_times = df[df['event_type'] == 'task_started'].merge(
    df[df['event_type'] == 'task_completed'],
    on=['participant_id', 'data_task_index'],
    suffixes=('_start', '_end')
)
task_times['duration'] = pd.to_datetime(task_times['timestamp_end']) - pd.to_datetime(task_times['timestamp_start'])

# Time series analysis
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour

# Count events by hour
hourly_activity = df.groupby('hour').size()
```

## Privacy Considerations

The logging system:
- **Participant IDs**: Users enter their own identifiers (e.g., P001, USER123)
- **No PII Collection**: The system does NOT automatically collect names, emails, or other personally identifiable information
- **Researcher Responsibility**: It is the researcher's responsibility to maintain a separate secure mapping between participant IDs and actual identities if needed
- **Anonymous IDs Recommended**: Consider using anonymous codes (P001, P002, etc.) rather than names
- **Random Session IDs**: Each session gets a unique random identifier
- **Local Storage**: All logs are stored locally on the server
- **Application Interactions Only**: Only user actions within the app are logged

## Disabling Logging

To disable logging, you can:

1. **Temporary:** Rename the `utils/user_logger.py` file
2. **Permanent:** Comment out the logger initialization in `app.py`

## Best Practices

1. **Regular Cleanup:** Periodically archive or delete old log files
2. **Storage Management:** Monitor the `evaluation_logs/` directory size
3. **Batch Analysis:** Analyze multiple sessions together for insights
4. **Backup:** Regularly backup log files for long-term studies

## Example Use Cases

### 1. Identify Struggling Users
```python
# Find sessions with many back steps
sessions_with_many_backs = [
    s for s in sessions
    if s['back_steps'] > s['total_steps'] * 0.3
]
```

### 2. Popular Graph Types
```python
# Count graph selections
from collections import Counter
graph_types = [
    e['data']['graph_type']
    for e in events
    if e['event_type'] == 'graph_selected'
]
Counter(graph_types).most_common()
```

### 3. Learning Progression
```python
# Compare quiz accuracy over time
quiz_events = [e for e in events if e['event_type'] == 'quiz_submitted']
accuracies = [e['data']['is_correct'] for e in quiz_events]
# Calculate moving average, etc.
```

## Troubleshooting

### No logs generated
- Check that `evaluation_logs/` directory exists and is writable
- Verify logger is initialized in `app.py`

### Incomplete logs
- Ensure `session_end` is called (check session handlers)
- Review server logs for errors

### Large log files
- Implement log rotation (not currently included)
- Export to database for better performance

## Future Enhancements

Potential improvements:
- Database storage (SQLite, PostgreSQL)
- Real-time dashboard
- Automated report generation
- Log rotation and compression
- Integration with analytics platforms
