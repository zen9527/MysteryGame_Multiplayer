import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict


class ScriptVersionRepository:
    """SQLite repository for script version management"""
    
    def __init__(self, db_path: str = "scripts.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Create script_versions table and indexes"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS script_versions (
                id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                notes TEXT,
                FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_script_versions_script_id ON script_versions(script_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_script_versions_created_at ON script_versions(created_at DESC)")
        self.conn.commit()
    
    def create_version(self, script_id: str, data: Dict, created_by: Optional[str] = None, notes: Optional[str] = None) -> str:
        """Create a new version for a script"""
        # Get the current max version number
        cursor = self.conn.execute(
            "SELECT MAX(version_number) FROM script_versions WHERE script_id = ?", (script_id,)
        )
        result = cursor.fetchone()
        version_number = (result[0] or 0) + 1
        
        version_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO script_versions (id, script_id, version_number, data, created_by, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (version_id, script_id, version_number, json.dumps(data), created_by, notes)
        )
        self.conn.commit()
        return version_id
    
    def get_version(self, version_id: str) -> Optional[Dict]:
        """Get a specific version by ID"""
        cursor = self.conn.execute(
            "SELECT * FROM script_versions WHERE id = ?", (version_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result["data"] = json.loads(result["data"])
        return result
    
    def get_script_versions(self, script_id: str) -> List[Dict]:
        """Get all versions for a script, ordered by version number DESC"""
        cursor = self.conn.execute(
            "SELECT * FROM script_versions WHERE script_id = ? ORDER BY version_number DESC",
            (script_id,)
        )
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["data"] = json.loads(result["data"])
            results.append(result)
        return results
    
    def get_latest_version(self, script_id: str) -> Optional[Dict]:
        """Get the latest version of a script"""
        cursor = self.conn.execute(
            """SELECT * FROM script_versions 
               WHERE script_id = ? 
               ORDER BY version_number DESC 
               LIMIT 1""", (script_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result["data"] = json.loads(result["data"])
        return result
    
    def restore_version(self, version_id: str) -> bool:
        """Restore a specific version (returns the restored data)"""
        version = self.get_version(version_id)
        if not version:
            return None
        
        # Create a new version with the restored data
        self.create_version(
            script_id=version["script_id"],
            data=version["data"],
            created_by="system",
            notes=f"Restored from version {version['version_number']} (id: {version_id})"
        )
        
        return version
    
    def compare_versions(self, version_id_1: str, version_id_2: str) -> Dict:
        """Compare two versions and return the differences"""
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        # Simple JSON diff
        import difflib
        
        def json_to_lines(obj):
            return json.dumps(obj, indent=2, ensure_ascii=False).splitlines(keepends=True)
        
        lines1 = json_to_lines(v1["data"])
        lines2 = json_to_lines(v2["data"])
        
        diff = list(difflib.unified_diff(lines1, lines2, fromfile=f"v{v1['version_number']}", tofile=f"v{v2['version_number']}"))
        
        return {
            "version_1": {
                "id": v1["id"],
                "version_number": v1["version_number"],
                "created_at": v1["created_at"]
            },
            "version_2": {
                "id": v2["id"],
                "version_number": v2["version_number"],
                "created_at": v2["created_at"]
            },
            "diff": diff
        }
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a specific version"""
        cursor = self.conn.execute(
            "DELETE FROM script_versions WHERE id = ?", (version_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def cleanup_old_versions(self, script_id: str, keep_last: int = 10) -> int:
        """Keep only the last N versions for a script"""
        # Get all version IDs except the last N
        cursor = self.conn.execute(
            """SELECT id FROM script_versions 
               WHERE script_id = ? 
               ORDER BY version_number DESC 
               LIMIT -1 OFFSET ?""",
            (script_id, keep_last)
        )
        old_versions = cursor.fetchall()
        
        deleted_count = 0
        for row in old_versions:
            self.conn.execute("DELETE FROM script_versions WHERE id = ?", (row[0],))
            deleted_count += 1
        
        if deleted_count > 0:
            self.conn.commit()
        
        return deleted_count
