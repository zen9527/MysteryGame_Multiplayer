# Script Center Design: Progressive Implementation

Date: 2026-05-13

## Goal

Build a comprehensive script management center for the Script Murder game, enabling users to browse, generate, edit, and import/export scripts through a modern UI with midnight purple-blue design system.

## Architecture

### Three-Phase Progressive Implementation

| Phase | Content | Duration | Deliverables |
|-------|---------|----------|--------------|
| 1 | Script browsing + detail preview | 1 day | `/scripts` route, 3 components |
| 2 | Script generation wizard | 1-2 days | `/scripts/generate`, SSE integration |
| 3 | Script editing + import/export | 1-2 days | `/scripts/edit/:id`, JSON editor |

**Total: 3-5 days**

---

## Phase 1: Script Browsing + Detail Preview

### Routes

```typescript
/scripts              → ScriptsPage.vue (main page with list + split view)
/scripts/:id          → ScriptDetail.vue (inline in split panel)
```

### Component Structure

```
client/src/components/scripts/
  ScriptsPage.vue      # Main page (list + split panel)
  ScriptCard.vue       # Script card component
  ScriptFilter.vue     # Filter component (genre/difficulty/player count)
```

### Features

- ✅ Script list display (card grid layout)
- ✅ Right-side split panel for detail preview (click card to expand)
- ✅ Filtering by genre, difficulty, player count
- ✅ Reuse existing `/api/scripts` endpoints

### Data Flow

```typescript
ScriptsPage → GET /api/scripts → List
ScriptCard click → GET /api/scripts/:id → Detail (split panel)
```

### Component Specifications

#### ScriptsPage.vue

```vue
<template>
  <div class="scripts-page">
    <!-- Header -->
    <header class="scripts-header">
      <h1>📚 剧本中心</h1>
      <button @click="navigateToGenerate" class="generate-btn">生成新剧本</button>
    </header>

    <!-- Filter Bar -->
    <ScriptFilter v-model="filters" @change="fetchScripts" />

    <!-- Main Content (Split View) -->
    <div class="split-view">
      <!-- Left: Script List -->
      <div class="script-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="scripts.length === 0" class="empty">暂无剧本</div>
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
        <ScriptDetail :script="selectedScript" @back="deselectScript" />
      </aside>
      <div class="detail-panel-placeholder" v-else>
        <p>点击左侧剧本查看详情</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '@/stores/game';
import ScriptCard from './ScriptCard.vue';
import ScriptFilter from './ScriptFilter.vue';
import ScriptDetail from './ScriptDetail.vue';

const router = useRouter();
const store = useGameStore();

const scripts = ref([]);
const filters = ref({ genre: '', difficulty: '', playerCount: '' });
const selectedScriptId = ref<string | null>(null);
const loading = ref(false);

const selectedScript = computed(() => 
  scripts.value.find(s => s.id === selectedScriptId.value)
);

async function fetchScripts() {
  loading.value = true;
  try {
    scripts.value = await store.fetchScripts(filters.value);
  } finally {
    loading.value = false;
  }
}

function selectScript(id: string) {
  selectedScriptId.value = id;
}

function deselectScript() {
  selectedScriptId.value = null;
}

function navigateToGenerate() {
  router.push('/scripts/generate');
}

onMounted(() => {
  fetchScripts();
});
</script>
```

#### ScriptCard.vue

```vue
<template>
  <div class="script-card" :class="{ active }">
    <div class="card-header">
      <h3>{{ script.title }}</h3>
      <span class="genre-tag">{{ script.genre }}</span>
    </div>
    <div class="card-meta">
      <span v-if="script.difficulty">{{ script.difficulty }}</span>
      <span v-if="script.player_count">{{ script.player_count }}人</span>
      <span v-if="script.created_at">{{ formatDate(script.created_at) }}</span>
    </div>
    <p class="card-desc">{{ script.description || script.background_story?.slice(0, 100) + '...' }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  script: any;
  active: boolean;
}>();

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN');
}
</script>
```

#### ScriptFilter.vue

```vue
<template>
  <div class="script-filter">
    <select v-model="localFilters.genre" @change="emitChange">
      <option value="">全部类型</option>
      <option value="悬疑推理">悬疑推理</option>
      <option value="古风权谋">古风权谋</option>
      <option value="现代都市">现代都市</option>
      <option value="恐怖惊悚">恐怖惊悚</option>
      <option value="欢乐搞笑">欢乐搞笑</option>
      <option value="科幻未来">科幻未来</option>
    </select>

    <select v-model="localFilters.difficulty" @change="emitChange">
      <option value="">全部难度</option>
      <option value="简单">简单</option>
      <option value="中等">中等</option>
      <option value="困难">困难</option>
    </select>

    <select v-model="localFilters.playerCount" @change="emitChange">
      <option value="">全部人数</option>
      <option value="3">3 人</option>
      <option value="4">4 人</option>
      <option value="5">5 人</option>
      <option value="6">6 人</option>
      <option value="7">7 人</option>
      <option value="8">8 人</option>
    </select>

    <button @click="resetFilters" class="reset-btn">重置</button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  modelValue: { genre: string; difficulty: string; playerCount: string };
}>();

const emit = defineEmits(['update:modelValue', 'change']);

const localFilters = ref({ ...props.modelValue });

watch(localFilters, (newVal) => {
  emit('update:modelValue', newVal);
}, { deep: true });

function emitChange() {
  emit('change');
}

function resetFilters() {
  localFilters.value = { genre: '', difficulty: '', playerCount: '' };
  emitChange();
}
</script>
```

### API Endpoints (Reuse)

```
GET    /api/scripts              # List with optional filters
GET    /api/scripts/:id          # Detail
DELETE /api/scripts/:id          # Delete (admin only)
```

---

## Phase 2: Script Generation Wizard

### Routes

```typescript
/scripts/generate     → ScriptGenerateWizard.vue
```

### Component Structure

```
client/src/components/scripts/
  ScriptGenerateWizard.vue  # Multi-step wizard
  WizardStep.vue            # Generic step component (optional)
```

### Wizard Flow

```
Step 1 (30s) → Step 2 (30s) → Step 3 (30s) → Step 4 (60-120s) → Step 5
   ↓            ↓            ↓              ↓               ↓
Select Genre  Select Difficulty  Player Count  LLM Generation  Confirm/Regenerate
```

### Features

- ✅ 5-step wizard UI with progress indicator
- ✅ SSE streaming generation display
- ✅ Real-time preview of generated script
- ✅ Confirm → Save to list / Regenerate → Back to Step 1

### Component Specification

#### ScriptGenerateWizard.vue

```vue
<template>
  <div class="script-wizard">
    <!-- Header -->
    <header class="wizard-header">
      <h1>🎭 生成新剧本</h1>
      <div class="progress-indicator">
        <span v-for="step in steps" :key="step" 
              :class="{ active: currentStep === step, completed: step < currentStep }">
          {{ step }}
        </span>
      </div>
    </header>

    <!-- Step Content -->
    <div class="wizard-content">
      <!-- Step 1: Genre Selection -->
      <div v-if="currentStep === 1" class="step-content">
        <h2>选择剧本类型</h2>
        <div class="genre-grid">
          <button v-for="genre in genres" :key="genre" 
                  @click="selectGenre(genre)" 
                  :class="{ selected: formData.genre === genre }">
            {{ genre }}
          </button>
        </div>
      </div>

      <!-- Step 2: Difficulty Selection -->
      <div v-if="currentStep === 2" class="step-content">
        <h2>选择难度</h2>
        <div class="difficulty-options">
          <button v-for="diff in difficulties" :key="diff"
                  @click="selectDifficulty(diff)"
                  :class="{ selected: formData.difficulty === diff }">
            {{ diff }}
          </button>
        </div>
      </div>

      <!-- Step 3: Player Count -->
      <div v-if="currentStep === 3" class="step-content">
        <h2>玩家数量</h2>
        <input type="range" v-model.number="formData.playerCount" 
               min="3" max="8" @input="updatePlayerCount" />
        <div class="player-display">{{ formData.playerCount }}人</div>
      </div>

      <!-- Step 4: LLM Generation -->
      <div v-if="currentStep === 4" class="step-content">
        <h2>正在生成剧本...</h2>
        <div v-if="generating" class="generation-status">
          <div class="spinner"></div>
          <p>{{ generationStatus }}</p>
        </div>
        <div v-if="generatedScript" class="preview-panel">
          <h3>预览</h3>
          <pre>{{ JSON.stringify(generatedScript, null, 2) }}</pre>
        </div>
      </div>

      <!-- Step 5: Confirm -->
      <div v-if="currentStep === 5" class="step-content">
        <h2>确认剧本</h2>
        <div class="final-preview">
          <ScriptDetail :script="generatedScript" />
        </div>
        <div class="wizard-actions">
          <button @click="confirmScript" class="confirm-btn">✅ 确认并保存</button>
          <button @click="regenerate" class="regen-btn">🔄 重新生成</button>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-nav" v-if="currentStep < 5">
      <button @click="prevStep" :disabled="currentStep === 1">← 上一步</button>
      <button @click="nextStep" :disabled="!canProceed">下一步 →</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '@/stores/game';
import ScriptDetail from './ScriptDetail.vue';

const router = useRouter();
const store = useGameStore();

const steps = [1, 2, 3, 4, 5];
const currentStep = ref(1);
const generating = ref(false);
const generationStatus = ref('');

const formData = ref({
  genre: '',
  difficulty: '',
  playerCount: 4,
});

const generatedScript = ref(null);

const genres = ['悬疑推理', '古风权谋', '现代都市', '恐怖惊悚', '欢乐搞笑', '科幻未来'];
const difficulties = ['简单', '中等', '困难'];

const canProceed = computed(() => {
  if (currentStep.value === 1) return formData.value.genre !== '';
  if (currentStep.value === 2) return formData.value.difficulty !== '';
  if (currentStep.value === 3) return true;
  if (currentStep.value === 4) return generatedScript.value !== null;
  return false;
});

function selectGenre(genre: string) {
  formData.value.genre = genre;
}

function selectDifficulty(difficulty: string) {
  formData.value.difficulty = difficulty;
}

function updatePlayerCount() {
  // Validation logic
}

async function nextStep() {
  if (currentStep.value === 3) {
    await generateScript();
  }
  currentStep.value++;
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
}

async function generateScript() {
  generating.value = true;
  generationStatus.value = '正在连接 LLM...';
  
  try {
    // SSE streaming generation
    const response = await fetch('/api/scripts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData.value),
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let accumulated = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      accumulated += chunk;
      
      // Parse SSE events
      generationStatus.value = '正在生成...';
    }
    
    generatedScript.value = JSON.parse(accumulated);
  } catch (error) {
    console.error('Generation failed:', error);
    alert('生成失败：' + error.message);
  } finally {
    generating.value = false;
  }
}

function confirmScript() {
  // Save script and redirect
  router.push('/scripts');
}

function regenerate() {
  currentStep.value = 1;
  generatedScript.value = null;
}
</script>
```

### API Endpoints (New)

```
POST   /api/scripts/generate     # SSE streaming generation
       Body: { genre, difficulty, player_count }
       Response: SSE stream → ScriptV2 JSON
```

---

## Phase 3: Script Editing + Import/Export

### Routes

```typescript
/scripts/edit/:id     → ScriptEditor.vue
/scripts/import       → ImportExportModal.vue (modal)
```

### Component Structure

```
client/src/components/scripts/
  ScriptEditor.vue        # JSON editor with syntax highlighting
  ImportExportModal.vue   # Import/export functionality
```

### Features

- ✅ JSON editor with syntax highlighting (use simple textarea or integrate Monaco)
- ✅ Manual editing of script fields
- ✅ Import JSON file
- ✅ Export JSON file
- ✅ Save to `/api/scripts/:id`

### Component Specification

#### ScriptEditor.vue

```vue
<template>
  <div class="script-editor">
    <header class="editor-header">
      <h1>编辑剧本</h1>
      <div class="editor-actions">
        <button @click="exportScript" class="export-btn">导出 JSON</button>
        <button @click="showImport = true" class="import-btn">导入 JSON</button>
        <button @click="saveScript" :disabled="saving" class="save-btn">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </header>

    <div class="editor-main">
      <textarea v-model="jsonContent" 
                class="json-editor"
                spellcheck="false"></textarea>
    </div>

    <!-- Validation Status -->
    <div v-if="validationError" class="validation-error">
      ⚠️ {{ validationError }}
    </div>
    <div v-if="validationSuccess" class="validation-success">
      ✅ 剧本格式正确
    </div>

    <!-- Import Modal -->
    <ImportExportModal v-if="showImport" 
                       @import="handleImport" 
                       @close="showImport = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import ImportExportModal from './ImportExportModal.vue';

const route = useRoute();
const scriptId = route.params.id as string;

const jsonContent = ref('');
const saving = ref(false);
const showImport = ref(false);
const validationError = ref('');
const validationSuccess = ref(false);

// Validate JSON
const isValidJson = computed(() => {
  try {
    JSON.parse(jsonContent.value);
    validationError.value = '';
    validationSuccess.value = true;
    return true;
  } catch (e) {
    validationError.value = e.message;
    validationSuccess.value = false;
    return false;
  }
});

onMounted(async () => {
  // Fetch script
  const response = await fetch(`/api/scripts/${scriptId}`);
  const script = await response.json();
  jsonContent.value = JSON.stringify(script, null, 2);
});

async function saveScript() {
  if (!isValidJson.value) return;
  
  saving.value = true;
  try {
    const script = JSON.parse(jsonContent.value);
    await fetch(`/api/scripts/${scriptId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(script),
    });
    alert('保存成功');
  } catch (error) {
    alert('保存失败：' + error.message);
  } finally {
    saving.value = false;
  }
}

function exportScript() {
  const blob = new Blob([jsonContent.value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `script-${scriptId}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function handleImport(json: string) {
  jsonContent.value = json;
  showImport.value = false;
}
</script>
```

#### ImportExportModal.vue

```vue
<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>导入剧本</h2>
      <textarea v-model="importContent" 
                placeholder="粘贴 JSON 内容..."
                rows="10"></textarea>
      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">取消</button>
        <button @click="confirmImport" :disabled="!isValidJson" class="confirm-btn">导入</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const emit = defineEmits(['close', 'import']);

const importContent = ref('');

const isValidJson = computed(() => {
  try {
    JSON.parse(importContent.value);
    return true;
  } catch {
    return false;
  }
});

function confirmImport() {
  emit('import', importContent.value);
}
</script>
```

### API Endpoints (New + Reuse)

```
PUT    /api/scripts/:id          # Update script
POST   /api/scripts/import       # Import script from JSON
GET    /api/scripts/:id          # Reused for editing
```

---

## State Management

### New Store: `stores/scripts.ts`

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ScriptMetadata, ScriptDetail } from '@/types/script';

export const useScriptStore = defineStore('scripts', () => {
  const scripts = ref<ScriptMetadata[]>([]);
  const currentScript = ref<ScriptDetail | null>(null);
  const filters = ref({ genre: '', difficulty: '', playerCount: '' });
  const loading = ref(false);

  async function fetchScripts(filter?: any) {
    loading.value = true;
    try {
      const response = await fetch('/api/scripts', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      scripts.value = await response.json();
    } finally {
      loading.value = false;
    }
  }

  async function fetchScriptDetail(id: string) {
    const response = await fetch(`/api/scripts/${id}`);
    currentScript.value = await response.json();
  }

  return {
    scripts,
    currentScript,
    filters,
    loading,
    fetchScripts,
    fetchScriptDetail,
  };
});
```

---

## Error Handling

### Frontend

- ✅ Loading states for all async operations
- ✅ Error messages for failed API calls
- ✅ JSON validation before save/import
- ✅ SSE error handling during generation

### Backend

- ✅ Validate script schema before save
- ✅ Rate limiting for generation endpoint
- ✅ Admin authentication for write operations

---

## Testing

### Unit Tests

- ScriptCard component (rendering, click events)
- ScriptFilter component (filter logic, reset)
- JSON validation utilities

### Integration Tests

- ScriptsPage → API integration
- Wizard flow → SSE generation
- Editor → Save/Import/Export

### E2E Tests

- Browse scripts → Select → View detail
- Generate wizard → Complete flow
- Edit script → Save → Verify

---

## Success Criteria

### Phase 1

- [ ] Scripts list displays correctly
- [ ] Split panel shows detail on click
- [ ] Filtering works (genre/difficulty/player count)
- [ ] Responsive design (mobile-friendly)

### Phase 2

- [ ] Wizard steps navigate correctly
- [ ] SSE generation displays in real-time
- [ ] Confirm saves script to list
- [ ] Regenerate returns to Step 1

### Phase 3

- [ ] JSON editor loads script content
- [ ] Save updates script via API
- [ ] Export downloads JSON file
- [ ] Import validates and loads JSON

---

## Risk Mitigation

1. **SSE Generation Timeout**: Add 120s timeout with user notification
2. **Large Script Files**: Limit import size to 500KB
3. **Concurrent Edits**: Show warning if script modified by another user
4. **LLM Errors**: Fallback to manual editing mode

---

## Future Extensions

- Script versioning (track edits over time)
- Script ratings and reviews
- Script templates (pre-defined structures)
- Collaborative editing (real-time)
