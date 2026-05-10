from typing import Optional, List, Dict
from server.models import ScriptMetadata, ScriptDetail
from server.script_repository import ScriptRepository


class ScriptService:
    """Business logic layer for script management with data masking"""
    
    def __init__(self, repository: ScriptRepository):
        self.repo = repository
    
    def list_scripts(self, genre: Optional[str] = None, difficulty: Optional[str] = None,
                     min_players: Optional[int] = None) -> List[Dict]:
        """List scripts with filters, returning metadata only (no sensitive data)"""
        scripts = self.repo.list_scripts(genre, difficulty, min_players)
        result = []
        for s in scripts:
            metadata = {
                "id": s["id"],
                "title": s["title"],
                "genre": s.get("genre"),
                "difficulty": s.get("difficulty"),
                "player_count": s.get("player_count"),
                "estimated_time": s.get("estimated_time"),
                "background_story": s.get("background_story"),
                "created_at": s.get("created_at")
            }
            result.append(metadata)
        return result
    
    def get_detail(self, script_id: str) -> Optional[Dict]:
        """Get script detail with masked sensitive fields (no true_killer, clues, etc.)"""
        script_data = self.repo.get(script_id)
        if not script_data:
            return None
        
        full_content = script_data["full_content"]
        detail = {
            "id": script_data["id"],
            "title": script_data["title"],
            "genre": script_data.get("genre"),
            "difficulty": script_data.get("difficulty"),
            "player_count": script_data.get("player_count"),
            "estimated_time": script_data.get("estimated_time"),
            "background_story": script_data.get("background_story"),
            "roles": full_content.get("roles", []),
            "plot_outline": full_content.get("plot_outline")
        }
        return detail
    
    def upload(self, script_data: Dict) -> str:
        """Upload a new script"""
        return self.repo.create(script_data)
    
    def delete(self, script_id: str) -> bool:
        """Soft delete a script"""
        return self.repo.soft_delete(script_id)
    
    def export_all(self) -> List[Dict]:
        """Export all active scripts"""
        return self.repo.export_all()
    
    def import_scripts(self, scripts: List[Dict]) -> int:
        """Import scripts"""
        return self.repo.import_scripts(scripts)
