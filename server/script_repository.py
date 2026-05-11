import sqlite3
import json
import uuid
from typing import Optional, List, Dict


class ScriptRepository:
    """SQLite repository for script persistence"""
    
    def __init__(self, db_path: str = "scripts.db"):
        import sys
        if sys.platform == "win32":
            # Windows SQLite needs UTF-8 encoding for Chinese characters
            self.conn = sqlite3.connect(db_path, check_same_thread=False, uri=True)
            self.conn.execute("PRAGMA encoding='UTF-8'")
        else:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Create scripts table and indexes"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                genre TEXT,
                difficulty TEXT,
                player_count INTEGER,
                estimated_time INTEGER,
                background_story TEXT,
                full_content JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_genre ON scripts(genre)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_difficulty ON scripts(difficulty)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_player_count ON scripts(player_count)")
        self.conn.commit()
    
    def create(self, script_data: Dict) -> str:
        """Create a new script and return its ID"""
        script_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO scripts (id, title, genre, difficulty, player_count, 
               estimated_time, background_story, full_content)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (script_id, script_data["title"], script_data.get("genre"),
             script_data.get("difficulty"), script_data.get("player_count"),
             script_data.get("estimated_time"), script_data.get("background_story"),
             json.dumps(script_data))
        )
        self.conn.commit()
        return script_id
    
    def get(self, script_id: str) -> Optional[Dict]:
        """Get a script by ID (only active scripts)"""
        cursor = self.conn.execute(
            "SELECT * FROM scripts WHERE id = ? AND is_active = 1", (script_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result["full_content"] = json.loads(result["full_content"])
        return result
    
    def list_scripts(self, genre: Optional[str] = None, difficulty: Optional[str] = None,
                     min_players: Optional[int] = None) -> List[Dict]:
        """List scripts with optional filters"""
        query = "SELECT * FROM scripts WHERE is_active = 1"
        params = []
        if genre:
            query += " AND genre = ?"
            params.append(genre)
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        if min_players:
            query += " AND player_count >= ?"
            params.append(min_players)
        cursor = self.conn.execute(query, params)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["full_content"] = json.loads(result["full_content"])
            results.append(result)
        return results
    
    def soft_delete(self, script_id: str) -> bool:
        """Soft delete a script by setting is_active to 0"""
        cursor = self.conn.execute(
            "UPDATE scripts SET is_active = 0 WHERE id = ?", (script_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def export_all(self) -> List[Dict]:
        """Export all active scripts"""
        cursor = self.conn.execute("SELECT * FROM scripts WHERE is_active = 1")
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["full_content"] = json.loads(result["full_content"])
            results.append(result)
        return results
    
    def import_scripts(self, scripts: List[Dict]) -> int:
        """Import scripts, generating IDs if missing"""
        count = 0
        for script in scripts:
            if "id" not in script:
                script["id"] = str(uuid.uuid4())
            self.conn.execute(
                """INSERT OR REPLACE INTO scripts 
                   (id, title, genre, difficulty, player_count, estimated_time, 
                    background_story, full_content)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (script["id"], script["title"], script.get("genre"),
                 script.get("difficulty"), script.get("player_count"),
                 script.get("estimated_time"), script.get("background_story"),
                 json.dumps(script))
            )
            count += 1
        self.conn.commit()
        return count
