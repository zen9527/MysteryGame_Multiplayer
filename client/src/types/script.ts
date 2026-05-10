export interface Role {
  id: string;
  name: string;
  age: number;
  occupation: string;
  description: string;
  background: string;
  secret_task: string;
  alibi: string;
  motive: string;
  relationships: Array<{ target: string; description: string }>;
}

export interface ScriptMetadata {
  id: string;
  title: string;
  genre?: string;
  difficulty?: string;
  player_count?: number;
  estimated_time?: number;
  background_story?: string;
  created_at?: string;
}

export interface ScriptDetail {
  id: string;
  title: string;
  genre?: string;
  difficulty?: string;
  player_count?: number;
  estimated_time?: number;
  background_story?: string;
  roles: Role[];
  plot_outline?: {
    act1: string;
    act2: string;
    act3: string;
  };
}

export interface ScriptFilters {
  genre?: string;
  difficulty?: string;
  min_players?: number;
}

export const scriptApi = {
  async listScripts(filters?: ScriptFilters): Promise<ScriptMetadata[]> {
    const params = new URLSearchParams();
    if (filters?.genre) params.set('genre', filters.genre);
    if (filters?.difficulty) params.set('difficulty', filters.difficulty);
    if (filters?.min_players) params.set('min_players', filters.min_players.toString());
    
    const response = await fetch(`/api/scripts?${params}`);
    const data = await response.json();
    return data.scripts;
  },

  async getDetail(scriptId: string): Promise<ScriptDetail> {
    const response = await fetch(`/api/scripts/${scriptId}`);
    return response.json();
  },

  async uploadScript(script: Omit<ScriptDetail, 'id'>): Promise<{ script_id: string }> {
    const response = await fetch('/api/scripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(script)
    });
    return response.json();
  }
};
