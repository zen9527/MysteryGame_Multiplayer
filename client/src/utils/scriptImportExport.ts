/**
 * Script Import/Export Utilities
 * Supports JSON format for data exchange
 */

/**
 * Export script to JSON file
 */
export function exportScriptToJSON(script: any): void {
  const dataStr = JSON.stringify(script, null, 2);
  const blob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${script.title || 'script'}_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Import script from JSON file
 */
export function importScriptFromJSON(file: File): Promise<any> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const script = JSON.parse(event.target?.result as string);
        
        // Basic validation
        if (!script.title || !script.roles) {
          reject(new Error('Invalid script format: missing required fields'));
          return;
        }
        
        // Ensure ID is set
        if (!script.id) {
          script.id = crypto.randomUUID();
        }
        
        resolve(script);
      } catch (error) {
        reject(new Error(`Failed to parse JSON: ${error instanceof Error ? error.message : 'Unknown error'}`));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
}

/**
 * Export multiple scripts to a single JSON file
 */
export function exportScriptsBatchJSON(scripts: any[]): void {
  const dataStr = JSON.stringify({ version: 1, exported_at: new Date().toISOString(), scripts }, null, 2);
  const blob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `scripts_batch_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Import multiple scripts from a batch JSON file
 */
export function importScriptsBatchJSON(file: File): Promise<any[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target?.result as string);
        
        // Check if it's a batch export
        if (data.scripts && Array.isArray(data.scripts)) {
          resolve(data.scripts);
        } else if (data.title && data.roles) {
          // Single script in batch format
          resolve([data]);
        } else {
          reject(new Error('Invalid batch import format'));
        }
      } catch (error) {
        reject(new Error(`Failed to parse JSON: ${error instanceof Error ? error.message : 'Unknown error'}`));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
}

/**
 * Convert script to Markdown format (for documentation)
 */
export function exportScriptToMarkdown(script: any): string {
  let md = `# ${script.title}\n\n`;
  
  if (script.genre) md += `**类型**: ${script.genre}\n`;
  if (script.difficulty) md += `**难度**: ${script.difficulty}\n`;
  if (script.player_count) md += `**人数**: ${script.player_count}人\n`;
  if (script.estimated_time) md += `**预计时间**: ${script.estimated_time}分钟\n\n`;
  
  if (script.background_story) {
    md += `## 背景故事\n\n${script.background_story}\n\n`;
  }
  
  if (script.roles && script.roles.length > 0) {
    md += `## 角色 (${script.roles.length}人)\n\n`;
    script.roles.forEach((role: any, index: number) => {
      md += `### ${index + 1}. ${role.name}\n`;
      if (role.age) md += `- **年龄**: ${role.age}\n`;
      if (role.occupation) md += `- **职业**: ${role.occupation}\n`;
      if (role.description) md += `- **描述**: ${role.description}\n\n`;
    });
  }
  
  if (script.clues && script.clues.length > 0) {
    md += `## 线索 (${script.clues.length}条)\n\n`;
    script.clues.forEach((clue: any, _index: number) => {
      md += `- **${clue.title}** (${clue.unlock_phase}): ${clue.content}\n`;
    });
  }
  
  return md;
}
