# Remote Logging Setup Guide

This document explains how to use the PathSolver remote logging system.

## Overview

The PathSolver application now supports sending logs to a separate logging server via HTTP. This allows you to:
- Monitor multiple PathSolver sessions in real-time
- Track which participants are active
- See what task each participant is currently working on
- View when the last update was received from each session

## Architecture

```
┌─────────────────┐         HTTP POST         ┌─────────────────────┐
│                 │  ────────────────────────> │                     │
│   PathSolver    │  Log events as JSON        │  Logging Server     │
│   Instance      │                            │  (Flask + SQLite)   │
│                 │                            │                     │
└─────────────────┘                            └─────────────────────┘
                                                         │
                                                         │
                                                         v
                                                ┌─────────────────┐
                                                │  Web Dashboard  │
                                                │  (Real-time UI) │
                                                └─────────────────┘
```

## Setup Instructions

### 1. Start the Logging Server

The logging server is located in: `/home/timo/pathsolver-logging-server/`

```bash
# Navigate to the logging server directory
cd /home/timo/pathsolver-logging-server

# Create and activate virtual environment (if not already done)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
./start_server.sh
# Or manually:
python app.py
```

The server will start on `http://localhost:5000`

### 2. Access the Dashboard

Open your web browser and go to:
```
http://localhost:5000
```

You'll see a real-time dashboard showing:
- **Active Sessions Count**: Number of currently active sessions
- **Total Events**: Total number of events logged
- **Session Cards**: One card per active session showing:
  - Participant ID
  - Session ID
  - Current task number and description (if in task mode)
  - Last event type
  - Time since last update
  - Total events from that session
  - Active/Recent status badge

The dashboard auto-refreshes every 5 seconds.

### 3. Configure PathSolver to Use Remote Logging

By default, remote logging is **enabled** and points to `http://157.180.50.44:5000/api/log`.

To configure it, set these environment variables before starting PathSolver:

```bash
# Enable remote logging (default: true)
export ENABLE_REMOTE_LOGGING=true

# URL of the logging server (default: http://157.180.50.44:5000/api/log)
export REMOTE_LOGGING_URL=http://localhost:5000/api/log

# Start PathSolver
python app.py
```

To disable remote logging:
```bash
export ENABLE_REMOTE_LOGGING=false
python app.py
```

### 4. Using with Multiple PathSolver Instances

You can run multiple PathSolver instances (on different ports or machines) all sending logs to the same logging server:

**Machine 1:**
```bash
export REMOTE_LOGGING_URL=http://logging-server-ip:5000/api/log
python app.py --port 8000
```

**Machine 2:**
```bash
export REMOTE_LOGGING_URL=http://logging-server-ip:5000/api/log
python app.py --port 8001
```

The logging server will track all sessions from all instances.

## Key Features

### Non-Blocking Logging
- Logs are sent in background threads
- App performance is not affected
- If the logging server is down, PathSolver continues working normally
- All logs are still saved locally as backup

### Session Tracking
A session is considered "active" if:
- It has received an event in the last 5 minutes
- It has not received a `session_end` event

Sessions are shown with badges:
- **ACTIVE** (green): Last update < 30 seconds ago
- **RECENT** (orange): Last update between 30 seconds and 5 minutes ago

### Task Tracking
When a participant is in task mode, the dashboard shows:
- Current task number
- Task description
- Task mode status

This is automatically updated with every event sent from PathSolver.

## API Endpoints

The logging server provides these endpoints:

### POST /api/log
Receives log events from PathSolver instances.

### GET /api/sessions/active
Returns JSON list of active sessions. Optional query parameter: `minutes` (default: 5)

### GET /api/sessions/{session_id}
Returns detailed information about a specific session including recent events.

### GET /health
Health check endpoint.

## Database

All logs are stored in SQLite database at:
```
/home/timo/pathsolver-logging-server/logs.db
```

You can query this database directly for analysis:
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('logs.db')
df = pd.read_sql_query("SELECT * FROM events", conn)
```

## Troubleshooting

### Logs not appearing in dashboard
1. Check that PathSolver has `ENABLE_REMOTE_LOGGING=true`
2. Verify the `REMOTE_LOGGING_URL` is correct
3. Check that the logging server is running
4. Look at the server logs for errors

### "Connection refused" errors
- The logging server is not running
- The URL/port is incorrect
- Firewall is blocking the connection

### Sessions not showing as active
- They may be older than 5 minutes
- Check the server time vs. PathSolver time (timezone issues)

## Files Modified in PathSolver

### utils/user_logger.py
- Added `requests` dependency for HTTP calls
- Added `ThreadPoolExecutor` for background requests
- Added `_send_http_log()` method
- Modified `_log_event()` to send HTTP requests

### requirements.txt
- Added `requests==2.31.0`

### EVALUATION_LOGGING.md
- Added documentation for remote logging configuration

## Separate Logging Server Repository

The logging server is in a separate git repository at:
```
/home/timo/pathsolver-logging-server/
```

This repository contains:
- `app.py` - Flask application
- `database.py` - Database operations
- `templates/index.html` - Dashboard UI
- `requirements.txt` - Dependencies
- `README.md` - Full documentation
- `start_server.sh` - Startup script

Git repository initialized with 3 commits:
1. Initial commit with all files
2. Add start server script
3. Fix datetime comparison issue

## Next Steps

1. **Production Deployment**: For production use, deploy the logging server with:
   - Gunicorn or another WSGI server
   - PostgreSQL instead of SQLite for better concurrency
   - Nginx reverse proxy
   - HTTPS/SSL

2. **Security**: Add authentication if needed:
   - API key for logging endpoint
   - Login for dashboard access

3. **Monitoring**: Set up alerts for:
   - Server downtime
   - Database size
   - Failed log deliveries

## Support

- PathSolver documentation: `EVALUATION_LOGGING.md`
- Logging server documentation: `/home/timo/pathsolver-logging-server/README.md`
