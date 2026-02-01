"""Session persistence utility for saving and restoring user sessions.

This module enables session state to persist across page reloads by:
1. Storing state in JSON files on the server
2. Using a persistent session ID stored in browser cookies
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import networkx as nx
from networkx.readwrite import json_graph


class SessionPersistence:
    """Handles saving and restoring session state to/from disk."""
    
    def __init__(self, storage_dir: str = "session_states"):
        """Initialize session persistence.
        
        Args:
            storage_dir: Directory to store session state files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get the file path for a session."""
        # Sanitize session ID to prevent path traversal
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.storage_dir / f"{safe_id}.json"
    
    def save_session(self, session_id: str, state_data: dict) -> bool:
        """Save session state to disk.
        
        Args:
            session_id: Unique session identifier
            state_data: Dictionary of state to persist (from StateManager.to_dict())
            
        Returns:
            True if save was successful
        """
        try:
            session_file = self._get_session_file(session_id)
            
            # Add metadata
            state_data["_metadata"] = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(session_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
            
            print(f"[SessionPersistence] Saved session {session_id}")
            return True
            
        except Exception as e:
            print(f"[SessionPersistence] Error saving session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[dict]:
        """Load session state from disk.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dictionary of saved state, or None if not found/invalid
        """
        try:
            session_file = self._get_session_file(session_id)
            
            if not session_file.exists():
                print(f"[SessionPersistence] No saved session found for {session_id}")
                return None
            
            with open(session_file, 'r') as f:
                state_data = json.load(f)
            
            print(f"[SessionPersistence] Loaded session {session_id}")
            return state_data
            
        except json.JSONDecodeError as e:
            print(f"[SessionPersistence] Corrupted session file for {session_id}: {e}")
            return None
        except Exception as e:
            print(f"[SessionPersistence] Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session file.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                session_file.unlink()
                print(f"[SessionPersistence] Deleted session {session_id}")
            return True
        except Exception as e:
            print(f"[SessionPersistence] Error deleting session {session_id}: {e}")
            return False
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session file exists."""
        return self._get_session_file(session_id).exists()
    
    def get_session_age_hours(self, session_id: str) -> Optional[float]:
        """Get the age of a session in hours.
        
        Returns:
            Age in hours, or None if session doesn't exist
        """
        try:
            session_file = self._get_session_file(session_id)
            if not session_file.exists():
                return None
            
            mtime = session_file.stat().st_mtime
            age_seconds = datetime.now().timestamp() - mtime
            return age_seconds / 3600
            
        except Exception:
            return None


# Graph serialization helpers
def serialize_graph(G: nx.Graph) -> dict:
    """Serialize a NetworkX graph to a JSON-compatible dictionary."""
    if G is None or len(G.nodes()) == 0:
        return None
    
    return json_graph.node_link_data(G)


def deserialize_graph(data: dict) -> nx.Graph:
    """Deserialize a graph from JSON data."""
    if data is None:
        return nx.Graph()
    
    try:
        return json_graph.node_link_graph(data)
    except Exception as e:
        print(f"[SessionPersistence] Error deserializing graph: {e}")
        return nx.Graph()


# Global persistence instance
_persistence = None


def get_persistence() -> SessionPersistence:
    """Get or create the global SessionPersistence instance."""
    global _persistence
    if _persistence is None:
        _persistence = SessionPersistence()
    return _persistence
