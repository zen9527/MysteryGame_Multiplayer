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

export interface RequestOptions {
  timeout?: number;
  signal?: AbortSignal;
}

import { fetchWithTimeout } from '@/utils/request';

export const scriptApi = {
  async listScripts(filters?: ScriptFilters, options?: RequestOptions): Promise<ScriptMetadata[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.genre) params.set('genre', filters.genre);
      if (filters?.difficulty) params.set('difficulty', filters.difficulty);
      if (filters?.min_players) params.set('min_players', filters.min_players.toString());
      
      const response = await fetchWithTimeout(`/api/scripts?${params}`, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      return data.scripts || [];
    } catch (error) {
      console.error('Failed to fetch scripts:', error);
      return [];
    }
  },

  async getDetail(scriptId: string, options?: RequestOptions): Promise<ScriptDetail> {
    try {
      const response = await fetchWithTimeout(`/api/scripts/${scriptId}`, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch script ${scriptId}:`, error);
      throw error;
    }
  },

  async uploadScript(script: Omit<ScriptDetail, 'id'>, options?: RequestOptions): Promise<{ script_id: string }> {
    try {
      const response = await fetchWithTimeout('/api/scripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(script),
        ...options,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to upload script:', error);
      throw error;
    }
  },

  async updateScript(scriptId: string, script: any, options?: RequestOptions): Promise<{ id: string; updated_at: string }> {
    try {
      const response = await fetchWithTimeout(`/api/scripts/${scriptId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(script),
        ...options,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to update script ${scriptId}:`, error);
      throw error;
    }
  },

  async deleteScript(scriptId: string, options?: RequestOptions): Promise<void> {
    try {
      const response = await fetchWithTimeout(`/api/scripts/${scriptId}`, {
        method: 'DELETE',
        ...options,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error(`Failed to delete script ${scriptId}:`, error);
      throw error;
    }
  }
};
