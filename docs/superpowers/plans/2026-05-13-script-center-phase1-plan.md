# Script Center Phase 1: Browsing + Detail Preview Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task.

**Goal:** Implement script browsing page with split-view layout (list + detail panel), filtering by genre/difficulty/player count.

**Architecture:** Split-view layout with left script list (card grid) and right detail panel. ScriptsPage.vue manages state. ScriptCard.vue renders scripts. ScriptFilter.vue handles filtering.

**Tech Stack:** Vue 3, TypeScript, Pinia, CSS custom properties

---

## File Structure

```
client/src/components/scripts/
  ScriptsPage.vue          # Create - main page with split view
  ScriptCard.vue           # Create - script card component  
  ScriptFilter.vue         # Create - filter component
client/src/router.ts       # Modify - add /scripts route
client/src/components/common/CollapsibleSidebar.vue  # Modify - add scripts nav
```

---

### Task 1: Create ScriptFilter Component

**Files:** Create `client/src/components/scripts/ScriptFilter.vue`

- [ ] **Write component**

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
      <option value="3">3 人</option><option value="4">4 人</option>
      <option value="5">5 人</option><option value="6">6 人</option>
      <option value="7">7 人</option><option value="8">8 人</option>
    </select>
    <button @click="resetFilters" class="reset-btn">重置</button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
export interface FilterValues { genre: string; difficulty: string; playerCount: string; }
const props = defineProps<{ modelValue: FilterValues; }>();
const emit = defineEmits(['update:modelValue', 'change']);
const localFilters = ref<FilterValues>({ ...props.modelValue });
watch(localFilters, (newVal) => emit('update:modelValue', newVal), { deep: true });
function emitChange() { emit('change'); }
function resetFilters() { localFilters.value = { genre: '', difficulty: '', playerCount: '' }; emitChange(); }
</script>

<style scoped>
@import '../../styles/variables.css';
.script-filter { display: flex; gap: var(--space-md); padding: var(--space-lg); background: var(--bg-secondary); border-radius: var(--radius-lg); margin-bottom: var(--space-lg); }
select { padding: var(--space-sm) var(--space-md); border: 1px solid var(--border-medium); border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-primary); font-size: 14px; }
.reset-btn { padding: var(--space-sm) var(--space-lg); border: none; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); cursor: pointer; }
.reset-btn:hover { background: var(--hover-bg); color: var(--text-primary); }
</style>
```

- [ ] **Commit:** `git add client/src/components/scripts/ScriptFilter.vue && git commit -m "feat: add ScriptFilter component"`

---

### Task 2: Create ScriptCard Component

**Files:** Create `client/src/components/scripts/ScriptCard.vue`

- [ ] **Write component**

```vue
<template>
  <div class="script-card" :class="{ active }">
    <div class="card-header"><h3>{{ script.title }}</h3><span class="genre-tag">{{ script.genre }}</span></div>
    <div class="card-meta">
      <span v-if="script.difficulty" class="difficulty-tag">{{ script.difficulty }}</span>
      <span v-if="script.player_count" class="player-tag">{{ script.player_count }}人</span>
      <span v-if="script.created_at" class="date-tag">{{ formatDate(script.created_at) }}</span>
    </div>
    <p v-if="script.description" class="card-desc">{{ truncate(script.description, 100) }}</p>
    <p v-else-if="script.background_story" class="card-desc">{{ truncate(script.background_story, 100) }}</p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ script: { id: string; title: string; genre: string; difficulty?: string; player_count?: number; created_at?: string; description?: string; background_story?: string; }; active: boolean; }>();
function formatDate(date: string): string { return new Date(date).toLocaleDateString('zh-CN'); }
function truncate(text: string, length: number): string { return text.length > length ? text.slice(0, length) + '...' : text; }
</script>

<style scoped>
@import '../../styles/variables.css';
.script-card { background: var(--bg-secondary); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: var(--space-lg); cursor: pointer; transition: all var(--transition-fast); }
.script-card:hover { border-color: var(--border-accent); transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.script-card.active { border-color: var(--accent-primary); background: var(--active-bg); }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-md); }
.card-header h3 { font-size: 16px; color: var(--text-primary); margin: 0; }
.genre-tag { padding: var(--space-xs) var(--space-sm); background: var(--accent-secondary); color: var(--bg-primary); border-radius: var(--radius-sm); font-size: 12px; }
.card-meta { display: flex; gap: var(--space-sm); margin-bottom: var(--space-md); flex-wrap: wrap; }
.difficulty-tag, .player-tag, .date-tag { font-size: 12px; color: var(--text-secondary); }
.card-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin: 0; }
</style>
```

- [ ] **Commit:** `git add client/src/components/scripts/ScriptCard.vue && git commit -m "feat: add ScriptCard component"`

---

### Task 3: Create ScriptsPage Component

**Files:** Create `client/src/components/scripts/ScriptsPage.vue`

- [ ] **Write component** (see full code in original plan - split-view with list + detail panel, fetchScripts, selectScript, deleteScript)

- [ ] **Commit:** `git add client/src/components/scripts/ScriptsPage.vue && git commit -m "feat: add ScriptsPage with split-view"`

---

### Task 4: Add Scripts Route

**Files:** Modify `client/src/router.ts`

- [ ] **Update router**

```typescript
import { createRouter, createWebHistory } from 'vue-router';
const RoomList = () => import('./components/RoomList.vue');
const RoomJoin = () => import('./components/RoomJoin.vue');
const WaitingLobby = () => import('./components/WaitingLobby.vue');
const GamePage = () => import('./components/GamePage.vue');
const RoomCreate = () => import('./pages/RoomCreate.vue');
const ScriptsPage = () => import('./components/scripts/ScriptsPage.vue');

const routes = [
  { path: '/', component: RoomList },
  { path: '/join/:gameId', component: RoomJoin },
  { path: '/lobby/:gameId', component: WaitingLobby },
  { path: '/game/:gameId', component: GamePage },
  { path: '/create', component: RoomCreate },
  { path: '/scripts', component: ScriptsPage },
  { path: '/scripts/generate', component: () => import('./components/scripts/ScriptGenerateWizard.vue'), meta: { placeholder: true } },
  { path: '/scripts/edit/:id', component: () => import('./components/scripts/ScriptEditor.vue'), meta: { placeholder: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
];

const router = createRouter({ history: createWebHistory(), routes });
export default router;
```

- [ ] **Commit:** `git add client/src/router.ts && git commit -m "feat: add /scripts route"`

---

### Task 5: Update Sidebar Navigation

**Files:** Modify `client/src/components/common/CollapsibleSidebar.vue`

- [ ] **Add scripts nav item** (already has it in current code - verify)

- [ ] **Commit:** `git add client/src/components/common/CollapsibleSidebar.vue && git commit -m "feat: verify scripts navigation"`

---

### Task 6: Verify Build and Test

- [ ] **Run build:** `cd client && npm run build` (expect success)
- [ ] **Run tests:** `cd client && npm test` (expect all pass)
- [ ] **Manual test:** Navigate to /scripts, click cards, test filtering, test delete
- [ ] **Commit:** `git commit --allow-empty -m "test: verify Phase 1 functionality"`

---

**Plan saved. Ready for inline execution.**
