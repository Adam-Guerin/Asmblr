#!/usr/bin/env python3
"""
TODO Tracker for Asmblr
Tracks and manages technical debt items
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any

class TodoTracker:
    """Manages and tracks TODO items"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.todo_file = root_path / "todos.json"
        self.todos = self._load_todos()
    
    def _load_todos(self) -> List[Dict[str, Any]]:
        """Load existing TODOs"""
        if self.todo_file.exists():
            with open(self.todo_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_todos(self):
        """Save TODOs to file"""
        with open(self.todo_file, 'w') as f:
            json.dump(self.todos, f, indent=2)
    
    def add_todo(self, file_path: str, line: int, description: str, severity: str = "medium"):
        """Add a new TODO item"""
        todo = {
            "id": len(self.todos) + 1,
            "file": file_path,
            "line": line,
            "description": description,
            "severity": severity,
            "status": "open",
            "created_at": time.time(),
            "assigned_to": None,
            "due_date": None
        }
        self.todos.append(todo)
        self._save_todos()
        return todo
    
    def resolve_todo(self, todo_id: int, resolution: str):
        """Mark a TODO as resolved"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["status"] = "resolved"
                todo["resolution"] = resolution
                todo["resolved_at"] = time.time()
                break
        self._save_todos()
    
    def get_open_todos(self) -> List[Dict[str, Any]]:
        """Get all open TODOs"""
        return [todo for todo in self.todos if todo["status"] == "open"]
    
    def get_todos_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get TODOs by severity"""
        return [todo for todo in self.todos if todo["severity"] == severity and todo["status"] == "open"]

def main():
    """Main TODO tracker"""
    import sys
    from pathlib import Path
    
    root_path = Path(__file__).parent.parent
    tracker = TodoTracker(root_path)
    
    if len(sys.argv) < 2:
        print("Usage: python todo_tracker.py [list|add|resolve]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        todos = tracker.get_open_todos()
        for todo in todos:
            print(f"#{todo['id']}: {todo['description']} ({todo['severity']}) - {todo['file']}")
    
    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: python todo_tracker.py add <file> <line> <description> [severity]")
            sys.exit(1)
        
        file_path = sys.argv[2]
        line = int(sys.argv[3])
        description = sys.argv[4]
        severity = sys.argv[5] if len(sys.argv) > 5 else "medium"
        
        todo = tracker.add_todo(file_path, line, description, severity)
        print(f"Added TODO #{todo['id']}")
    
    elif command == "resolve":
        if len(sys.argv) < 4:
            print("Usage: python todo_tracker.py resolve <id> <resolution>")
            sys.exit(1)
        
        todo_id = int(sys.argv[2])
        resolution = sys.argv[3]
        
        tracker.resolve_todo(todo_id, resolution)
        print(f"Resolved TODO #{todo_id}")

if __name__ == "__main__":
    main()
