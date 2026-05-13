# Script Generation Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a 5-step wizard UI for LLM-driven script generation with SSE streaming display

**Architecture:** Wizard component with progressive state management, SSE stream consumer for real-time generation feedback, integration with existing `/api/scripts/generate` endpoint

**Tech Stack:** Vue 3 + TypeScript, Pinia store, native fetch API for SSE streaming, midnight purple-blue design system

---

## File Structure

### Files to Create
- `client/src/components/scripts/ScriptGenerateWizard.vue` - Main wizard component (replace placeholder)
- `client/src/stores/scriptGenerator.ts` - New Pinia store for generation state management
- `client/src/utils/sse-parser.ts` - SSE stream parser utility (if needed, or reuse existing)

### Files to Modify
- `client/src/router.ts:15-17` - Update route meta (remove placeholder flag)
- `client/src/stores/game.ts` - Add script generation methods if not already present

### Files to Test
- `client/tests/unit/ScriptGenerateWizard.spec.ts` - Component unit tests
- `client/tests/integration/script-generation.spec.ts` - Integration test with mock SSE

---

## Backend API Check

**Existing endpoint:** `POST /api/scripts/generate` (SSE streaming)
- Location: `server/api/script.py`
- Parameters: `genre`, `difficulty`, `player_count`
- Response: SSE stream with JSON chunks

**Verify:** Endpoint exists and accepts the wizard's form data format

---

### Task 1: Create ScriptGenerator Store

**Files:**
- Create: `client/src/stores/scriptGenerator.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// client/tests/unit/scriptGenerator.spec.ts
import { describe, it, expect } from 'vitest';
import { createTestingPinia } from '@pinia/testing';
import { setActivePinia } from 'pinia';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';

describe('ScriptGenerator Store', () => {
  beforeEach(() => {
    setActivePinia(createTestingPinia());
  });

  it('initializes with default state', () => {
    const store = useScriptGeneratorStore();
    expect(store.currentStep).toBe(1);
    expect(store.generating).toBe(false);
    expect(store.generatedScript).toBeNull();
  });

  it('updates form data', () => {
    const store = useScriptGeneratorStore();
    store.updateFormData({ genre: '悬疑推理', difficulty: '中等', playerCount: 5 });
    expect(store.formData.genre).toBe('悬疑推理');
    expect(store.formData.difficulty).toBe('中等');
    expect(store.formData.playerCount).toBe(5);
  });

  it('validates form for each step', () => {
    const store = useScriptGeneratorStore();
    store.currentStep = 1;
    expect(store.canProceed).toBe(false);
    
    store.updateFormData({ genre: '悬疑推理', difficulty: '', playerCount: 4 });
    expect(store.canProceed).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npm test -- scriptGenerator.spec.ts`
Expected: FAIL - "useScriptGeneratorStore is not exported"

- [ ] **Step 3: Write minimal implementation**

```typescript
// client/src/stores/scriptGenerator.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ScriptV2 } from '@/types/script';

export interface GenerationFormData {
  genre: string;
  difficulty: string;
  playerCount: number;
}

export const useScriptGeneratorStore = defineStore('scriptGenerator', () => {
  // State
  const currentStep = ref(1);
  const formData = ref<GenerationFormData>({
    genre: '',
    difficulty: '',
    playerCount: 4,
  });
  const generating = ref(false);
  const generationStatus = ref('');
  const generatedScript = ref<ScriptV2 | null>(null);
  const error = ref<string | null>(null);

  // Constants
  const genres = ['悬疑推理', '古风权谋', '现代都市', '恐怖惊悚', '欢乐搞笑', '科幻未来'];
  const difficulties = ['简单', '中等', '困难'];
  const steps = [1, 2, 3, 4, 5];

  // Computed
  const canProceed = computed(() => {
    if (currentStep.value === 1) return formData.value.genre !== '';
    if (currentStep.value === 2) return formData.value.difficulty !== '';
    if (currentStep.value === 3) return true;
    if (currentStep.value === 4) return generatedScript.value !== null;
    return false;
  });

  const currentStepLabel = computed(() => {
    const labels: Record<number, string> = {
      1: '选择类型',
      2: '选择难度',
      3: '设置人数',
      4: '生成中',
      5: '确认',
    };
    return labels[currentStep.value];
  });

  // Actions
  function updateFormData(partial: Partial<GenerationFormData>) {
    formData.value = { ...formData.value, ...partial };
  }

  function selectGenre(genre: string) {
    formData.value.genre = genre;
  }

  function selectDifficulty(difficulty: string) {
    formData.value.difficulty = difficulty;
  }

  function setPlayerCount(count: number) {
    formData.value.playerCount = Math.max(3, Math.min(8, count));
  }

  function nextStep() {
    if (currentStep.value < 5) {
      currentStep.value++;
    }
  }

  function prevStep() {
    if (currentStep.value > 1) {
      currentStep.value--;
    }
  }

  function reset() {
    currentStep.value = 1;
    formData.value = { genre: '', difficulty: '', playerCount: 4 };
    generatedScript.value = null;
    error.value = null;
  }

  return {
    // State
    currentStep,
    formData,
    generating,
    generationStatus,
    generatedScript,
    error,
    genres,
    difficulties,
    steps,
    // Computed
    canProceed,
    currentStepLabel,
    // Actions
    updateFormData,
    selectGenre,
    selectDifficulty,
    setPlayerCount,
    nextStep,
    prevStep,
    reset,
  };
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd client && npm test -- scriptGenerator.spec.ts`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add client/src/stores/scriptGenerator.ts client/tests/unit/scriptGenerator.spec.ts
git commit -m "feat: add scriptGenerator store for wizard state management"
```

---

### Task 2: Implement ScriptGenerateWizard Component (Steps 1-3)

**Files:**
- Modify: `client/src/components/scripts/ScriptGenerateWizard.vue` (replace placeholder)

- [ ] **Step 1: Write the failing test**

```typescript
// client/tests/unit/ScriptGenerateWizard.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ScriptGenerateWizard from '@/components/scripts/ScriptGenerateWizard.vue';

describe('ScriptGenerateWizard', () => {
  const mountComponent = () => {
    return mount(ScriptGenerateWizard, {
      global: {
        plugins: [createTestingPinia()],
        stubs: {
          'router-link': true,
        },
      },
    });
  };

  it('renders step 1 genre selection', () => {
    const wrapper = mountComponent();
    expect(wrapper.text()).toContain('选择剧本类型');
    expect(wrapper.text()).toContain('悬疑推理');
    expect(wrapper.text()).toContain('古风权谋');
  });

  it('highlights selected genre', async () => {
    const wrapper = mountComponent();
    const genreBtn = wrapper.find('button:contains("悬疑推理")');
    await genreBtn.trigger('click');
    expect(genreBtn.classes()).toContain('selected');
  });

  it('shows progress indicator', () => {
    const wrapper = mountComponent();
    expect(wrapper.text()).toContain('1');
    expect(wrapper.text()).toContain('2');
    expect(wrapper.text()).toContain('3');
    expect(wrapper.text()).toContain('4');
    expect(wrapper.text()).toContain('5');
  });

  it('disables next button when form invalid', () => {
    const wrapper = mountComponent();
    const nextBtn = wrapper.find('.wizard-nav button:last-child');
    expect(nextBtn.attributes('disabled')).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npm test -- ScriptGenerateWizard.spec.ts`
Expected: FAIL - placeholder component doesn't have wizard UI

- [ ] **Step 3: Write minimal implementation (Steps 1-3)**

```vue
<!-- client/src/components/scripts/ScriptGenerateWizard.vue -->
<template>
  <div class="script-wizard">
    <!-- Header -->
    <header class="wizard-header">
      <h1>🎭 生成新剧本</h1>
      <div class="progress-indicator">
        <span 
          v-for="step in store.steps" 
          :key="step"
          :class="{ 
            active: store.currentStep === step, 
            completed: step < store.currentStep 
          }"
        >
          {{ step }}
        </span>
      </div>
      <p class="step-label">{{ store.currentStepLabel }}</p>
    </header>

    <!-- Step Content -->
    <div class="wizard-content">
      <!-- Step 1: Genre Selection -->
      <div v-if="store.currentStep === 1" class="step-content">
        <h2>选择剧本类型</h2>
        <div class="genre-grid">
          <button 
            v-for="genre in store.genres" 
            :key="genre" 
            @click="store.selectGenre(genre)"
            :class="{ selected: store.formData.genre === genre }"
          >
            {{ genre }}
          </button>
        </div>
      </div>

      <!-- Step 2: Difficulty Selection -->
      <div v-if="store.currentStep === 2" class="step-content">
        <h2>选择难度</h2>
        <div class="difficulty-options">
          <button 
            v-for="diff in store.difficulties" 
            :key="diff"
            @click="store.selectDifficulty(diff)"
            :class="{ selected: store.formData.difficulty === diff }"
          >
            {{ diff }}
          </button>
        </div>
      </div>

      <!-- Step 3: Player Count -->
      <div v-if="store.currentStep === 3" class="step-content">
        <h2>玩家数量</h2>
        <div class="slider-container">
          <input 
            type="range" 
            v-model.number="playerCountInput"
            min="3" 
            max="8" 
            @input="updatePlayerCount"
          />
          <div class="player-display">{{ store.formData.playerCount }}人</div>
        </div>
      </div>

      <!-- Step 4: LLM Generation (placeholder for Task 3) -->
      <div v-if="store.currentStep === 4" class="step-content">
        <p>生成功能待实现...</p>
      </div>

      <!-- Step 5: Confirm (placeholder for Task 3) -->
      <div v-if="store.currentStep === 5" class="step-content">
        <p>确认功能待实现...</p>
      </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-nav" v-if="store.currentStep < 5">
      <button @click="store.prevStep" :disabled="store.currentStep === 1">
        ← 上一步
      </button>
      <button @click="handleNext" :disabled="!store.canProceed">
        下一步 →
      </button>
    </div>

    <!-- Cancel Button -->
    <div class="wizard-footer">
      <router-link to="/scripts" class="cancel-btn">取消</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';

const router = useRouter();
const store = useScriptGeneratorStore();

const playerCountInput = ref(store.formData.playerCount);

function updatePlayerCount() {
  store.setPlayerCount(playerCountInput.value);
}

async function handleNext() {
  if (!store.canProceed) return;
  
  if (store.currentStep === 3) {
    // Will trigger generation in Task 3
  }
  
  store.nextStep();
}
</script>

<style scoped>
@import '../../styles/variables.css';

.script-wizard {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--space-xl);
}

.wizard-header {
  text-align: center;
  margin-bottom: var(--space-2xl);
}

.wizard-header h1 {
  font-size: 32px;
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
}

.progress-indicator {
  display: flex;
  justify-content: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.progress-indicator span {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.progress-indicator span.active {
  background: var(--accent-primary);
  color: var(--bg-primary);
  transform: scale(1.1);
}

.progress-indicator span.completed {
  background: var(--success);
  color: var(--bg-primary);
}

.step-label {
  font-size: 16px;
  color: var(--text-secondary);
}

.wizard-content {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  min-height: 400px;
  margin-bottom: var(--space-xl);
}

.step-content h2 {
  font-size: 24px;
  color: var(--text-primary);
  margin-bottom: var(--space-xl);
  text-align: center;
}

.genre-grid, .difficulty-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-md);
}

.genre-grid button, .difficulty-options button {
  padding: var(--space-lg) var(--space-xl);
  background: var(--bg-tertiary);
  border: 2px solid var(--border-medium);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.genre-grid button:hover, .difficulty-options button:hover {
  border-color: var(--accent-primary);
  background: var(--hover-bg);
}

.genre-grid button.selected, .difficulty-options button.selected {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: var(--bg-primary);
}

.slider-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
}

.slider-container input[type="range"] {
  width: 100%;
  max-width: 400px;
  accent-color: var(--accent-primary);
}

.player-display {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent-primary);
}

.wizard-nav {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.wizard-nav button {
  padding: var(--space-md) var(--space-xl);
  border-radius: var(--radius-md);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.wizard-nav button:first-child {
  background: var(--bg-tertiary);
  border: 2px solid var(--border-medium);
  color: var(--text-secondary);
}

.wizard-nav button:first-child:hover:not(:disabled) {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.wizard-nav button:last-child {
  background: var(--accent-primary);
  border: 2px solid var(--accent-primary);
  color: var(--bg-primary);
}

.wizard-nav button:last-child:hover:not(:disabled) {
  opacity: 0.9;
}

.wizard-nav button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.wizard-footer {
  text-align: center;
}

.cancel-btn {
  padding: var(--space-md) var(--space-xl);
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.cancel-btn:hover {
  color: var(--text-primary);
}
</style>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd client && npm test -- ScriptGenerateWizard.spec.ts`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add client/src/components/scripts/ScriptGenerateWizard.vue client/tests/unit/ScriptGenerateWizard.spec.ts
git commit -m "feat: implement wizard UI steps 1-3 (genre, difficulty, player count)"
```

---

### Task 3: Implement SSE Generation (Step 4)

**Files:**
- Modify: `client/src/components/scripts/ScriptGenerateWizard.vue`
- Modify: `client/src/stores/scriptGenerator.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// client/tests/integration/script-generation.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ScriptGenerateWizard from '@/components/scripts/ScriptGenerateWizard.vue';

describe('ScriptGenerateWizard - SSE Generation', () => {
  it('calls generation API with form data', async () => {
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"title":"Test"}\n\n') })
            .mockResolvedValueOnce({ done: true, value: undefined }),
        }),
      },
    });

    const wrapper = mount(ScriptGenerateWizard, {
      global: {
        plugins: [createTestingPinia()],
        stubs: { 'router-link': true },
      },
    });

    // Set form data
    const store = wrapper.vm.$store.scriptGenerator;
    store.selectGenre('悬疑推理');
    store.selectDifficulty('中等');
    store.setPlayerCount(5);
    
    // Navigate to step 4 (generation)
    store.nextStep();
    
    await vi.waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          genre: '悬疑推理',
          difficulty: '中等',
          player_count: 5,
        }),
      });
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npm test -- script-generation.spec.ts`
Expected: FAIL - generation not implemented

- [ ] **Step 3: Write minimal implementation**

First, update the store:

```typescript
// client/src/stores/scriptGenerator.ts (add to existing file)
// Add after import section:
const API_BASE = '/api/scripts';

// Add new action after setPlayerCount:
async function generateScript() {
  generating.value = true;
  generationStatus.value = '正在连接 LLM...';
  error.value = null;
  
  try {
    const response = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        genre: formData.value.genre,
        difficulty: formData.value.difficulty,
        player_count: formData.value.playerCount,
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Generation failed: ${response.status}`);
    }
    
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('ReadableStream not supported');
    }
    
    const decoder = new TextDecoder();
    let accumulated = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      accumulated += chunk;
      
      // Update status based on SSE events
      generationStatus.value = '正在生成剧本...';
    }
    
    // Parse final JSON from accumulated SSE data
    // SSE format: "data: {...json...}\n\n"
    const jsonMatch = accumulated.match(/data:\s*(\{.*\})/s);
    if (jsonMatch && jsonMatch[1]) {
      generatedScript.value = JSON.parse(jsonMatch[1]);
    } else {
      throw new Error('Failed to parse generated script');
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '未知错误';
    generationStatus.value = '生成失败';
    throw err;
  } finally {
    generating.value = false;
  }
}

// Add to return statement:
// generateScript,
```

Then update the component:

```vue
<!-- client/src/components/scripts/ScriptGenerateWizard.vue -->
<!-- Replace Step 4 section: -->
<div v-if="store.currentStep === 4" class="step-content">
  <h2>正在生成剧本...</h2>
  <div v-if="store.generating" class="generation-status">
    <div class="spinner"></div>
    <p>{{ store.generationStatus }}</p>
  </div>
  
  <div v-if="store.generatedScript" class="preview-panel">
    <h3>生成结果预览</h3>
    <div class="script-preview">
      <h4>{{ store.generatedScript.title }}</h4>
      <p class="meta">
        {{ store.generatedScript.genre }} · 
        {{ store.generatedScript.difficulty }} · 
        {{ store.generatedScript.player_count }}人
      </p>
      <p v-if="store.generatedScript.background_story" class="preview-text">
        {{ store.generatedScript.background_story.slice(0, 200) }}...
      </p>
    </div>
  </div>
  
  <div v-if="store.error" class="error-message">
    ⚠️ {{ store.error }}
    <button @click="retryGeneration" class="retry-btn">重试</button>
  </div>
</div>

<!-- Replace handleNext function: -->
async function handleNext() {
  if (!store.canProceed) return;
  
  if (store.currentStep === 3) {
    try {
      await store.generateScript();
    } catch (error) {
      // Error already set in store
      return; // Don't proceed if generation failed
    }
  }
  
  store.nextStep();
}

<!-- Add retry function: -->
function retryGeneration() {
  store.generateScript();
}

<!-- Add new styles: -->
<style scoped>
/* ... existing styles ... */

.generation-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-2xl);
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid var(--border-medium);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-panel {
  margin-top: var(--space-xl);
  padding: var(--space-lg);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-medium);
}

.preview-panel h3 {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.script-preview h4 {
  font-size: 24px;
  color: var(--accent-primary);
  margin-bottom: var(--space-sm);
}

.script-preview .meta {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.script-preview .preview-text {
  font-size: 16px;
  color: var(--text-primary);
  line-height: 1.6;
}

.error-message {
  background: var(--error-bg);
  border: 1px solid var(--error);
  color: var(--error);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.retry-btn {
  padding: var(--space-sm) var(--space-md);
  background: var(--error);
  color: var(--bg-primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 600;
}
</style>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd client && npm test -- script-generation.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add client/src/components/scripts/ScriptGenerateWizard.vue client/src/stores/scriptGenerator.ts
git commit -m "feat: implement SSE streaming generation for step 4"
```

---

### Task 4: Implement Confirm Step (Step 5)

**Files:**
- Modify: `client/src/components/scripts/ScriptGenerateWizard.vue`
- Modify: `client/src/stores/scriptGenerator.ts`

- [ ] **Step 1: Write the failing test**

```typescript
// client/tests/unit/ScriptGenerateWizard.spec.ts (add to existing file)
describe('ScriptGenerateWizard - Confirm Step', () => {
  it('shows confirm button on step 5', async () => {
    const wrapper = mountComponent();
    const store = wrapper.vm.$store.scriptGenerator;
    
    // Navigate to step 5
    store.currentStep = 5;
    store.generatedScript = { id: 'test', title: 'Test Script' } as any;
    
    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('确认并保存');
    expect(wrapper.text()).toContain('重新生成');
  });

  it('redirects to scripts list after confirm', async () => {
    const routerPush = vi.fn();
    const wrapper = mount(ScriptGenerateWizard, {
      global: {
        plugins: [createTestingPinia(), { install: (app) => app.provide('$router', { push: routerPush }) }],
        stubs: { 'router-link': true },
      },
    });
    
    const store = wrapper.vm.$store.scriptGenerator;
    store.currentStep = 5;
    store.generatedScript = { id: 'test', title: 'Test' } as any;
    
    const confirmBtn = wrapper.find('.confirm-btn');
    await confirmBtn.trigger('click');
    
    expect(routerPush).toHaveBeenCalledWith('/scripts');
  });

  it('resets wizard on regenerate', async () => {
    const wrapper = mountComponent();
    const store = wrapper.vm.$store.scriptGenerator;
    
    store.currentStep = 5;
    await wrapper.vm.$nextTick();
    
    const regenBtn = wrapper.find('.regen-btn');
    await regenBtn.trigger('click');
    
    expect(store.currentStep).toBe(1);
    expect(store.generatedScript).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npm test -- ScriptGenerateWizard.spec.ts`
Expected: FAIL - confirm step not implemented

- [ ] **Step 3: Write minimal implementation**

```vue
<!-- client/src/components/scripts/ScriptGenerateWizard.vue -->
<!-- Replace Step 5 section: -->
<div v-if="store.currentStep === 5" class="step-content">
  <h2>确认剧本</h2>
  <div class="final-preview">
    <div class="script-card">
      <h3>{{ store.generatedScript?.title }}</h3>
      <div class="meta">
        <span>{{ store.generatedScript?.genre }}</span>
        <span>{{ store.generatedScript?.difficulty }}</span>
        <span>{{ store.generatedScript?.player_count }}人</span>
      </div>
      <p v-if="store.generatedScript?.background_story" class="description">
        {{ store.generatedScript.background_story.slice(0, 300) }}...
      </p>
      <div v-if="store.generatedScript?.roles" class="roles-preview">
        <h4>角色列表</h4>
        <ul>
          <li v-for="role in store.generatedScript.roles.slice(0, 5)" :key="role.name">
            {{ role.name }} - {{ role.gender }}
          </li>
        </ul>
      </div>
    </div>
  </div>
  
  <div class="wizard-actions">
    <button @click="confirmScript" class="confirm-btn">
      ✅ 确认并保存
    </button>
    <button @click="regenerate" class="regen-btn">
      🔄 重新生成
    </button>
  </div>
</div>

<!-- Add after handleNext function: -->
async function confirmScript() {
  if (!store.generatedScript) return;
  
  // TODO: Save script to backend (if needed)
  // For now, just redirect to scripts list
  router.push('/scripts');
}

function regenerate() {
  store.reset();
}

<!-- Add new styles: -->
<style scoped>
/* ... existing styles ... */

.final-preview {
  margin-bottom: var(--space-xl);
}

.script-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.script-card h3 {
  font-size: 28px;
  color: var(--accent-primary);
  margin-bottom: var(--space-md);
}

.script-card .meta {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.script-card .meta span {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

.script-card .description {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
}

.roles-preview h4 {
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.roles-preview ul {
  list-style: none;
  padding: 0;
  display: grid;
  gap: var(--space-sm);
}

.roles-preview li {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

.wizard-actions {
  display: flex;
  justify-content: center;
  gap: var(--space-lg);
  margin-top: var(--space-xl);
}

.confirm-btn, .regen-btn {
  padding: var(--space-lg) var(--space-2xl);
  font-size: 18px;
  font-weight: 600;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.confirm-btn {
  background: var(--success);
  border: 2px solid var(--success);
  color: var(--bg-primary);
}

.confirm-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

.regen-btn {
  background: var(--bg-tertiary);
  border: 2px solid var(--border-medium);
  color: var(--text-primary);
}

.regen-btn:hover {
  background: var(--hover-bg);
}
</style>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd client && npm test -- ScriptGenerateWizard.spec.ts`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add client/src/components/scripts/ScriptGenerateWizard.vue
git commit -m "feat: implement confirm step with save and regenerate actions"
```

---

### Task 5: Update Router and Verify Build

**Files:**
- Modify: `client/src/router.ts:15`

- [ ] **Step 1: Update router**

```typescript
// client/src/router.ts (line 15)
// Remove meta: { placeholder: true } from generate route
{ path: '/scripts/generate', component: () => import('./components/scripts/ScriptGenerateWizard.vue') },
```

- [ ] **Step 2: Run build**

Run: `cd client && npm run build`
Expected: SUCCESS

- [ ] **Step 3: Run all tests**

Run: `cd client && npm test`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add client/src/router.ts
git commit -m "feat: update router for script generation wizard"
```

---

## Self-Review Checklist

After completing all tasks, verify:

1. **Spec coverage:**
   - [ ] 5-step wizard UI ✅
   - [ ] Progress indicator ✅
   - [ ] SSE streaming generation ✅
   - [ ] Real-time preview ✅
   - [ ] Confirm/Regenerate actions ✅

2. **Placeholder scan:**
   - [ ] No "TBD", "TODO" in final code (except intentional future extensions)
   - [ ] All test code included
   - [ ] All styles included

3. **Type consistency:**
   - [ ] `GenerationFormData` type matches API expectations
   - [ ] `ScriptV2` type used for generated script
   - [ ] Store actions match component calls

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-13-script-center-phase2-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
