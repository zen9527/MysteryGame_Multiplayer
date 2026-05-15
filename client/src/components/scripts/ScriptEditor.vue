<template>
  <div class="script-editor">
    <!-- Header -->
    <header class="editor-header">
      <div class="header-left">
        <router-link to="/scripts" class="back-btn">← 返回</router-link>
        <h1>编辑剧本：{{ script.title || '新剧本' }}</h1>
      </div>
      <div class="header-actions">
        <button @click="handleUndo" :disabled="!canUndo" class="action-btn">撤销</button>
        <button @click="handleRedo" :disabled="!canRedo" class="action-btn">重做</button>
        <span class="save-status" :class="{ saving: isSaving, saved: isSaved }">
          {{ saveStatusText }}
        </span>
        <button @click="handleSave" :disabled="isSaving" class="save-btn">
          {{ isSaving ? '保存中...' : '保存' }}
        </button>
        <button @click="handleExport" class="export-btn">导出</button>
        <button @click="showVersionHistory = true" class="version-btn">版本历史</button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="editor-main">
      <!-- Sidebar -->
      <aside class="editor-sidebar">
        <nav class="section-nav">
          <button v-for="section in sections" :key="section.id" @click="activeSection = section.id"
            :class="{ active: activeSection === section.id }" class="nav-item">
            {{ section.label }}
            <span v-if="section.badge" class="badge">{{ section.badge }}</span>
          </button>
        </nav>
      </aside>

      <!-- Content -->
      <main class="editor-content">
        <!-- Metadata -->
        <div v-show="activeSection === 'metadata'" class="section-panel">
          <h2>基本信息</h2>
          <div class="form-grid">
            <div class="form-group full-width">
              <label>剧本标题 *</label>
              <input v-model="script.title" type="text" placeholder="输入剧本标题" />
            </div>
            <div class="form-group">
              <label>类型 *</label>
              <select v-model="script.genre">
                <option value="">请选择</option>
                <option value="悬疑推理">悬疑推理</option>
                <option value="古风权谋">古风权谋</option>
                <option value="现代都市">现代都市</option>
                <option value="恐怖惊悚">恐怖惊悚</option>
                <option value="欢乐搞笑">欢乐搞笑</option>
                <option value="科幻未来">科幻未来</option>
              </select>
            </div>
            <div class="form-group">
              <label>难度 *</label>
              <select v-model="script.difficulty">
                <option value="">请选择</option>
                <option value="简单">简单</option>
                <option value="中等">中等</option>
                <option value="困难">困难</option>
              </select>
            </div>
            <div class="form-group">
              <label>人数 *</label>
              <input v-model.number="script.player_count" type="number" min="3" max="8" />
            </div>
            <div class="form-group">
              <label>预计时间 (分钟)</label>
              <input v-model.number="script.estimated_time" type="number" min="60" max="240" />
            </div>
            <div class="form-group full-width">
              <label>背景故事</label>
              <textarea v-model="script.background_story" rows="6"></textarea>
            </div>
          </div>
        </div>

        <!-- Roles -->
        <div v-show="activeSection === 'roles'" class="section-panel">
          <div class="panel-header">
            <h2>角色管理</h2>
            <button @click="addRole" class="add-btn">+ 添加角色</button>
          </div>
          <div v-if="!script.roles || script.roles.length === 0" class="empty-state">
            <p>暂无角色</p>
            <button @click="addRole" class="empty-action">添加第一个角色</button>
          </div>
          <div v-else>
            <div v-for="(role, index) in script.roles" :key="role.id" class="card">
              <div class="card-header">
                <span>{{ index + 1 }}.</span>
                <input v-model="role.name" type="text" placeholder="角色名" class="name-input" />
                <button @click="removeRole(index)" class="remove-btn">×</button>
              </div>
              <div class="form-grid">
                <div class="form-group"><label>年龄</label><input v-model.number="role.age" type="number" /></div>
                <div class="form-group"><label>职业</label><input v-model="role.occupation" type="text" /></div>
                <div class="form-group full-width"><label>描述</label><textarea v-model="role.description" rows="2"></textarea></div>
                <div class="form-group full-width"><label>背景</label><textarea v-model="role.background" rows="3"></textarea></div>
                <div class="form-group full-width"><label>秘密任务</label><textarea v-model="role.secret_task" rows="2"></textarea></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Clues -->
        <div v-show="activeSection === 'clues'" class="section-panel">
          <div class="panel-header">
            <h2>线索管理</h2>
            <button @click="addClue" class="add-btn">+ 添加线索</button>
          </div>
          <div v-if="!script.clues || script.clues.length === 0" class="empty-state">
            <p>暂无线索</p>
            <button @click="addClue" class="empty-action">添加第一个线索</button>
          </div>
          <div v-else>
            <div v-for="(clue, index) in script.clues" :key="clue.id" class="card">
              <div class="card-header">
                <span>{{ index + 1 }}.</span>
                <input v-model="clue.title" type="text" placeholder="线索标题" class="name-input" />
                <select v-model="clue.unlock_phase" class="phase-select">
                  <option value="act1">Act 1</option>
                  <option value="act2">Act 2</option>
                </select>
                <button @click="removeClue(index)" class="remove-btn">×</button>
              </div>
              <div class="form-group full-width"><label>内容</label><textarea v-model="clue.content" rows="3"></textarea></div>
            </div>
          </div>
        </div>

        <!-- NPCs -->
        <div v-show="activeSection === 'npcs'" class="section-panel">
          <div class="panel-header">
            <h2>NPC 管理</h2>
            <button @click="addNPC" class="add-btn">+ 添加 NPC</button>
          </div>
          <div v-if="!script.npcs || script.npcs.length === 0" class="empty-state">
            <p>暂无 NPC</p>
            <button @click="addNPC" class="empty-action">添加第一个 NPC</button>
          </div>
          <div v-else>
            <div v-for="(npc, index) in script.npcs" :key="index" class="card">
              <div class="card-header">
                <span>{{ index + 1 }}.</span>
                <input v-model="npc.name" type="text" placeholder="NPC 名称" class="name-input" />
                <button @click="removeNPC(index)" class="remove-btn">×</button>
              </div>
              <div class="form-grid">
                <div class="form-group"><label>年龄</label><input v-model.number="npc.age" type="number" /></div>
                <div class="form-group"><label>职业</label><input v-model="npc.occupation" type="text" /></div>
                <div class="form-group full-width"><label>描述</label><textarea v-model="npc.description" rows="2"></textarea></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Details -->
        <div v-show="activeSection === 'details'" class="section-panel">
          <h2>其他信息</h2>
          <div class="form-group full-width">
            <label>氛围描述</label>
            <textarea v-model="script.atmosphere" rows="4"></textarea>
          </div>
        </div>
      </main>
    </div>

    <!-- Version History Modal -->
    <VersionHistory 
      v-if="showVersionHistory" 
      :script-id="scriptId"
      @close="showVersionHistory = false"
      @version-restored="handleVersionRestored"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { scriptApi } from '@/types/script';
import { exportScriptToJSON } from '@/utils/scriptImportExport';
import VersionHistory from './VersionHistory.vue';

const route = useRoute();
const router = useRouter();

const scriptId = ref(route.params.id as string);
const isSaving = ref(false);
const isSaved = ref(true);
const activeSection = ref('metadata');

const history = ref<any[]>([]);
const historyIndex = ref(-1);
const showVersionHistory = ref(false);

const script = ref<any>({
  id: '',
  title: '',
  genre: '',
  difficulty: '',
  player_count: 4,
  estimated_time: 90,
  background_story: '',
  roles: [],
  clues: [],
  npcs: [],
  atmosphere: '',
});

const sections = computed(() => [
  { id: 'metadata', label: '基本信息' },
  { id: 'roles', label: '角色管理', badge: script.value.roles?.length || 0 },
  { id: 'clues', label: '线索管理', badge: script.value.clues?.length || 0 },
  { id: 'npcs', label: 'NPC 管理', badge: script.value.npcs?.length || 0 },
  { id: 'details', label: '其他信息' },
]);

const canUndo = computed(() => historyIndex.value > 0);
const canRedo = computed(() => historyIndex.value < history.value.length - 1);
const saveStatusText = computed(() => {
  if (isSaving.value) return '保存中...';
  if (isSaved.value) return '已保存';
  return '未保存';
});

onMounted(async () => {
  if (scriptId.value && scriptId.value !== 'new') {
    await loadScript(scriptId.value);
  } else {
    script.value.id = crypto.randomUUID();
  }
  pushHistory();
});

watch(script, () => {
  isSaved.value = false;
}, { deep: true });

async function loadScript(id: string) {
  try {
    const data = await scriptApi.getDetail(id);
    script.value = { ...data, id };
  } catch (error) {
    console.error('Failed to load script:', error);
    router.push('/scripts');
  }
}

function pushHistory() {
  history.value = history.value.slice(0, historyIndex.value + 1);
  history.value.push(JSON.parse(JSON.stringify(script.value)));
  historyIndex.value = history.value.length - 1;
  if (history.value.length > 50) {
    history.value.shift();
    historyIndex.value--;
  }
}

function handleUndo() {
  if (canUndo.value) {
    historyIndex.value--;
    script.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]));
    isSaved.value = true;
  }
}

function handleRedo() {
  if (canRedo.value) {
    historyIndex.value++;
    script.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]));
    isSaved.value = true;
  }
}

async function handleSave() {
  isSaving.value = true;
  try {
    await scriptApi.updateScript(script.value.id, script.value);
    isSaved.value = true;
    pushHistory();
  } catch (error) {
    console.error('Failed to save script:', error);
  } finally {
    isSaving.value = false;
  }
}

function handleExport() {
  exportScriptToJSON(script.value);
}

function handleVersionRestored(newVersionId: string) {
  console.log('Version restored:', newVersionId);
  // Reload the script after restore
  if (scriptId.value) {
    loadScript(scriptId.value);
  }
}

function addRole() {
  if (!script.value.roles) script.value.roles = [];
  script.value.roles.push({ id: crypto.randomUUID(), name: '', age: 0, occupation: '', description: '', background: '', secret_task: '' });
  pushHistory();
}

function removeRole(index: number) {
  script.value.roles.splice(index, 1);
  pushHistory();
}

function addClue() {
  if (!script.value.clues) script.value.clues = [];
  script.value.clues.push({ id: crypto.randomUUID(), title: '', content: '', unlock_phase: 'act1' });
  pushHistory();
}

function removeClue(index: number) {
  script.value.clues.splice(index, 1);
  pushHistory();
}

function addNPC() {
  if (!script.value.npcs) script.value.npcs = [];
  script.value.npcs.push({ name: '', age: 0, occupation: '', description: '' });
  pushHistory();
}

function removeNPC(index: number) {
  script.value.npcs.splice(index, 1);
  pushHistory();
}
</script>

<style scoped>
@import '@/styles/variables.css';

.script-editor { min-height: 100vh; background: var(--bg-primary); color: var(--text-primary); }
.editor-header { display: flex; justify-content: space-between; align-items: center; padding: var(--space-lg) var(--space-xl); background: var(--bg-secondary); border-bottom: 1px solid var(--border-light); position: sticky; top: 0; z-index: 100; }
.header-left { display: flex; align-items: center; gap: var(--space-lg); }
.back-btn { color: var(--text-secondary); text-decoration: none; font-size: 14px; }
.editor-header h1 { font-size: 20px; margin: 0; }
.header-actions { display: flex; align-items: center; gap: var(--space-md); }
.action-btn, .save-btn, .export-btn, .version-btn { padding: var(--space-sm) var(--space-md); border: 1px solid var(--border-medium); background: var(--bg-primary); color: var(--text-primary); border-radius: var(--radius-md); cursor: pointer; font-size: 14px; }
.action-btn:hover:not(:disabled), .export-btn, .version-btn { background: var(--bg-secondary); border-color: var(--accent-primary); }
.action-btn:disabled { opacity: 0.5; }
.save-btn { background: var(--accent-primary); border-color: var(--accent-primary); color: white; }
.save-status { font-size: 12px; color: var(--text-secondary); }
.save-status.saved { color: var(--accent-success); }

.editor-main { display: flex; height: calc(100vh - 70px); }
.editor-sidebar { width: min(200px, 20vw); background: var(--bg-secondary); border-right: 1px solid var(--border-light); padding: var(--space-md); overflow-y: auto; }
.section-nav { display: flex; flex-direction: column; gap: var(--space-xs); }
.nav-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-md); background: transparent; border: none; color: var(--text-secondary); cursor: pointer; border-radius: var(--radius-md); text-align: left; font-size: 14px; white-space: nowrap; }
.nav-item:hover { background: var(--bg-primary); color: var(--text-primary); }
.nav-item.active { background: var(--accent-primary-light); color: var(--accent-primary); font-weight: 600; }
.badge { background: var(--bg-tertiary); padding: 2px 8px; border-radius: var(--radius-round); font-size: 12px; }

.editor-content { flex: 1; padding: var(--space-xl); overflow-y: auto; max-width: 900px; margin: 0 auto; }
.section-panel { max-width: 800px; margin: 0 auto; }
.section-panel h2 { font-size: 24px; margin-bottom: var(--space-xl); }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-xl); }
.add-btn { padding: var(--space-sm) var(--space-md); background: var(--accent-primary); color: white; border: none; border-radius: var(--radius-md); cursor: pointer; }

.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-lg); margin-bottom: var(--space-xl); }
.form-group { display: flex; flex-direction: column; gap: var(--space-sm); }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-size: 14px; font-weight: 500; color: var(--text-secondary); }
.form-group input, .form-group select, .form-group textarea { padding: var(--space-md); border: 1px solid var(--border-medium); border-radius: var(--radius-md); background: var(--bg-primary); color: var(--text-primary); font-size: 14px; font-family: inherit; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: var(--accent-primary); }

.card { background: var(--bg-secondary); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: var(--space-xl); margin-bottom: var(--space-lg); }
.card-header { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-lg); }
.card-header span { font-weight: 600; color: var(--text-secondary); min-width: 30px; }
.name-input { flex: 1; padding: var(--space-sm) var(--space-md); border: 1px solid var(--border-medium); border-radius: var(--radius-md); background: var(--bg-primary); color: var(--text-primary); font-size: 16px; font-weight: 500; }
.phase-select { padding: var(--space-sm) var(--space-md); border: 1px solid var(--border-medium); border-radius: var(--radius-md); background: var(--bg-primary); color: var(--text-primary); }
.remove-btn { width: 28px; height: 28px; border: none; background: var(--bg-tertiary); color: var(--text-secondary); border-radius: var(--radius-round); cursor: pointer; font-size: 18px; line-height: 1; }
.remove-btn:hover { background: var(--accent-danger); color: white; }

.empty-state { text-align: center; padding: var(--space-3xl); background: var(--bg-secondary); border-radius: var(--radius-lg); border: 1px dashed var(--border-medium); }
.empty-state p { color: var(--text-secondary); margin-bottom: var(--space-lg); }
.empty-action { padding: var(--space-md) var(--space-xl); background: var(--accent-primary); color: white; border: none; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; }
</style>
