# PathSolver User Action Logging System

This document describes the comprehensive user action logging system implemented for evaluating how users interact with the PathSolver application.

## Overview

The logging system captures all user interactions with the application, including:
- Algorithm execution steps
- Graph manipulations
- Prediction game interactions
- Solution quiz submissions
- Settings changes
- Session metadata

All logs are stored in JSONL (JSON Lines) format for easy analysis.

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
  "event_type": "algorithm_step",
  "data": {
    "step_number": 1,
    "step_name": "visit_neighbors",
    "current_node": "5",
    "nodes_visited": ["1", "5"]
  }
}
```

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

# Filter by event type
algo_steps = df[df['event_type'] == 'algorithm_step']

# Time series analysis
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour

# Count events by hour
hourly_activity = df.groupby('hour').size()
```

## Privacy Considerations

The logging system:
- Does NOT log any personally identifiable information (PII)
- Uses random session IDs (not linked to user accounts)
- Only logs application interactions, not user identity
- Stores logs locally on the server

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
