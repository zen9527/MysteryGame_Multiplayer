<template>
  <div class="scripts-page">
    <!-- Header -->
    <header class="scripts-header">
      <h1>📚 剧本中心</h1>
      <router-link to="/scripts/generate" class="generate-btn">
        生成新剧本 →
      </router-link>
    </header>

    <!-- Filter Bar -->
    <ScriptFilter v-model="filters" @change="fetchScripts" />

    <!-- Main Content (Split View) -->
    <div class="split-view">
      <!-- Left: Script List -->
      <div class="script-list">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="scripts.length === 0" class="empty-state">
          <p>暂无剧本</p>
          <router-link to="/scripts/generate" class="empty-action">
            生成第一个剧本
          </router-link>
        </div>
        <ScriptCard
          v-for="script in scripts"
          :key="script.id"
          :script="script"
          :active="selectedScriptId === script.id"
          @click="selectScript(script.id)"
        />
      </div>

      <!-- Right: Detail Panel -->
      <aside class="detail-panel" v-if="selectedScript">
        <div class="panel-header">
          <h2>{{ selectedScript.title }}</h2>
          <button @click="deselectScript" class="close-btn">×</button>
        </div>
        <div class="panel-content">
          <div class="script-info">
            <span class="info-label">类型：</span>
            <span class="info-value">{{ selectedScript.genre }}</span>
          </div>
          <div class="script-info" v-if="selectedScript.difficulty">
            <span class="info-label">难度：</span>
            <span class="info-value">{{ selectedScript.difficulty }}</span>
          </div>
          <div class="script-info" v-if="selectedScript.player_count">
            <span class="info-label">人数：</span>
            <span class="info-value">{{ selectedScript.player_count }}人</span>
          </div>
          <div class="script-info" v-if="selectedScript.created_at">
            <span class="info-label">创建时间：</span>
            <span class="info-value">{{ formatDate(selectedScript.created_at) }}</span>
          </div>
          
          <details open class="detail-section">
            <summary>背景故事</summary>
            <p class="detail-text">{{ selectedScript.background_story || '暂无' }}</p>
          </details>

          <details open class="detail-section" v-if="selectedScript.roles?.length">
            <summary>角色列表 ({{ selectedScript.roles.length }}人)</summary>
            <div v-for="(role, i) in selectedScript.roles" :key="i" class="role-item">
              <strong>{{ role.name }}</strong> — {{ role.occupation }}, {{ role.age }}岁
              <p class="role-desc">{{ role.description || '' }}</p>
            </div>
          </details>

          <details class="detail-section" v-if="selectedScript.clues?.length">
            <summary>线索 ({{ selectedScript.clues.length }}条)</summary>
            <div v-for="(clue, i) in selectedScript.clues" :key="i" class="clue-item">
              <strong>{{ clue.title }}</strong>: {{ clue.content }}
            </div>
          </details>

          <div class="panel-actions">
            <router-link 
              :to="`/scripts/edit/${selectedScript.id}`" 
              class="edit-btn"
            >
              编辑剧本
            </router-link>
            <button @click="deleteScript" class="delete-btn">删除剧本</button>
          </div>
        </div>
      </aside>
      <div class="detail-panel-placeholder" v-else>
        <p>点击左侧剧本查看详情</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import ScriptCard from './ScriptCard.vue';
import ScriptFilter, { type FilterValues } from './ScriptFilter.vue';

interface ScriptMetadata {
  id: string;
  title: string;
  genre: string;
  difficulty?: string;
  player_count?: number;
  created_at?: string;
  description?: string;
  background_story?: string;
  roles?: Array<{ name: string; occupation: string; age: number; description?: string }>;
  clues?: Array<{ title: string; content: string }>;
}

const scripts = ref<ScriptMetadata[]>([]);
const filters = ref<FilterValues>({ genre: '', difficulty: '', playerCount: '' });
const selectedScriptId = ref<string | null>(null);
const loading = ref(false);

const selectedScript = ref<ScriptMetadata | null>(null);

async function fetchScripts() {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (filters.value.genre) params.set('genre', filters.value.genre);
    if (filters.value.difficulty) params.set('difficulty', filters.value.difficulty);
    if (filters.value.playerCount) params.set('player_count', filters.value.playerCount);
    
    const response = await fetch(`/api/scripts?${params}`);
    if (!response.ok) throw new Error('Failed to fetch scripts');
    scripts.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch scripts:', error);
    scripts.value = [];
  } finally {
    loading.value = false;
  }
}

function selectScript(id: string) {
  selectedScriptId.value = id;
  const script = scripts.value.find(s => s.id === id);
  if (script) {
    selectedScript.value = { ...script };
    fetchScriptDetails(id);
  }
}

async function fetchScriptDetails(id: string) {
  try {
    const response = await fetch(`/api/scripts/${id}`);
    if (!response.ok) throw new Error('Failed to fetch details');
    selectedScript.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch script details:', error);
  }
}

function deselectScript() {
  selectedScriptId.value = null;
  selectedScript.value = null;
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('zh-CN');
}

async function deleteScript() {
  if (!selectedScript.value) return;
  if (!confirm(`确定删除剧本"${selectedScript.value.title}"吗？`)) return;
  
  try {
    const response = await fetch(`/api/scripts/${selectedScript.value.id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete');
    
    deselectScript();
    await fetchScripts();
    alert('剧本已删除');
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    console.error('Failed to delete script:', error);
    alert('删除失败：' + errorMessage);
  }
}

onMounted(() => {
  fetchScripts();
});
</script>

<style scoped>
@import '../../styles/variables.css';

.scripts-page {
  padding: var(--space-xl);
  height: calc(100vh - 80px);
  overflow-y: auto;
}

.scripts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xl);
}

.scripts-header h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin: 0;
}

.generate-btn {
  padding: var(--space-md) var(--space-xl);
  background: var(--accent-primary);
  color: var(--bg-primary);
  border-radius: var(--radius-md);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.generate-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.split-view {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: var(--space-lg);
  height: calc(100% - 120px);
}

.script-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
  overflow-y: auto;
  padding-right: var(--space-sm);
}

.loading-state, .empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-medium);
  border-top-color: var(--accent-primary);
  border-radius: var(--radius-round);
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-md);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-action {
  margin-top: var(--space-md);
  color: var(--accent-primary);
  text-decoration: none;
}

.detail-panel {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-medium);
}

.panel-header h2 {
  font-size: 18px;
  color: var(--text-primary);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 20px;
}

.panel-content {
  padding: var(--space-lg);
  flex: 1;
  overflow-y: auto;
}

.script-info {
  display: flex;
  margin-bottom: var(--space-sm);
}

.info-label {
  color: var(--text-secondary);
  margin-right: var(--space-sm);
}

.info-value {
  color: var(--text-primary);
}

.detail-section {
  margin-top: var(--space-lg);
  border-top: 1px solid var(--border-light);
  padding-top: var(--space-md);
}

.detail-section summary {
  cursor: pointer;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-text {
  margin-top: var(--space-md);
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.role-item, .clue-item {
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--border-light);
}

.role-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: var(--space-xs);
}

.panel-actions {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-medium);
}

.edit-btn, .delete-btn {
  flex: 1;
  padding: var(--space-md);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.edit-btn {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  text-decoration: none;
  text-align: center;
}

.edit-btn:hover {
  background: var(--hover-bg);
}

.delete-btn {
  background: rgba(233, 69, 96, 0.2);
  color: #e94560;
}

.delete-btn:hover {
  background: rgba(233, 69, 96, 0.3);
}

.detail-panel-placeholder {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}
</style>
