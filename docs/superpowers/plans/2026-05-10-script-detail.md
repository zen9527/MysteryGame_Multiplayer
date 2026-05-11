# ScriptDetail Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create ScriptDetail.vue component that displays full script information with sensitive fields masked, plus comprehensive tests.

**Architecture:** Single Vue 3 component with props-based scriptId, emits back/start events. Fetches data via scriptApi.getDetail(). Shows loading/error states. Sensitive fields (true_killer, murder_method, clues, private_events) are NOT displayed.

**Tech Stack:** Vue 3 + TypeScript, Vitest, @vue/test-utils, Pydantic v2 backend API

---

## File Structure

**Create:**
- `client/src/components/ScriptDetail.vue` - Main component with masked content display
- `client/src/components/__tests__/ScriptDetail.spec.ts` - Component tests

**Dependencies:**
- `client/src/types/script.ts` - ScriptDetail interface, scriptApi.getDetail() (already exists per spec)

---

### Task 1: Write component test

**Files:**
- Create: `client/src/components/__tests__/ScriptDetail.spec.ts`

- [ ] **Step 1: Write the failing test**

```typescript
import { mount } from '@vue/test-utils';
import ScriptDetail from '@/components/ScriptDetail.vue';
import { scriptApi } from '@/types/script';

vi.mock('@/types/script', () => ({
  scriptApi: {
    getDetail: vi.fn()
  }
}));

describe('ScriptDetail', () => {
  it('loads and displays script detail', async () => {
    vi.mocked(scriptApi.getDetail).mockResolvedValue({
      id: '1',
      title: 'Test Script',
      genre: '悬疑推理',
      difficulty: '中等',
      player_count: 6,
      estimated_time: 120,
      background_story: 'Test story',
      roles: [{ id: '1', name: '角色 A', age: 30, occupation: '医生', description: '描述', background: '背景', secret_task: '任务', alibi: '不在场证明' }],
      plot_outline: { act1: '第一幕', act2: '第二幕', act3: '第三幕' }
    });

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('Test Script');
    expect(wrapper.text()).toContain('角色 A');
  });

  it('hides sensitive fields', async () => {
    vi.mocked(scriptApi.getDetail).mockResolvedValue({
      id: '1',
      title: 'Test Script',
      roles: [],
      plot_outline: { act1: '第一幕', act2: '第二幕', act3: '第三幕' }
    });

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).not.toContain('true_killer');
    expect(wrapper.text()).not.toContain('murder_method');
    expect(wrapper.text()).not.toContain('clues');
  });

  it('shows loading state', async () => {
    vi.mocked(scriptApi.getDetail).mockImplementation(() => new Promise(() => {}));

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    expect(wrapper.text()).toContain('加载中...');
  });

  it('shows error when load fails', async () => {
    vi.mocked(scriptApi.getDetail).mockRejectedValue(new Error('Failed'));

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('加载剧本失败');
  });

  it('emits back and start events', async () => {
    vi.mocked(scriptApi.getDetail).mockResolvedValue({
      id: '1',
      title: 'Test Script',
      roles: [],
      plot_outline: { act1: '', act2: '', act3: '' }
    });

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();

    const backBtn = wrapper.find('.back-btn');
    await backBtn.trigger('click');
    expect(wrapper.emitted('back')).toBeTruthy();

    const startBtn = wrapper.find('.start-btn');
    await startBtn.trigger('click');
    expect(wrapper.emitted('start')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd client && npm test -- ScriptDetail.spec.ts`
Expected: FAIL - "Cannot find module '@/components/ScriptDetail.vue'"

- [ ] **Step 3: Commit**

```bash
git add client/src/components/__tests__/ScriptDetail.spec.ts
git commit -m "test: add ScriptDetail component tests"
```

---

### Task 2: Create ScriptDetail.vue component

**Files:**
- Create: `client/src/components/ScriptDetail.vue`

- [ ] **Step 1: Write minimal implementation**

```vue
<template>
  <div class="script-detail">
    <button @click="$emit('back')" class="back-btn">← 返回列表</button>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="script" class="content">
      <h1>{{ script.title }}</h1>
      
      <div class="meta">
        <span v-if="script.genre">类型：{{ script.genre }}</span>
        <span v-if="script.difficulty">难度：{{ script.difficulty }}</span>
        <span v-if="script.player_count">人数：{{ script.player_count }}人</span>
        <span v-if="script.estimated_time">时长：{{ script.estimated_time }}分钟</span>
      </div>

      <section class="background">
        <h2>背景故事</h2>
        <p>{{ script.background_story }}</p>
      </section>

      <section class="roles">
        <h2>角色列表</h2>
        <div v-for="role in script.roles" :key="role.id" class="role-card">
          <h3>{{ role.name }}</h3>
          <p><strong>年龄：</strong>{{ role.age }}</p>
          <p><strong>职业：</strong>{{ role.occupation }}</p>
          <p><strong>描述：</strong>{{ role.description }}</p>
        </div>
      </section>

      <section class="plot-outline">
        <h2>剧情大纲</h2>
        <div v-if="script.plot_outline">
          <div class="act"><strong>第一幕：</strong>{{ script.plot_outline.act1 }}</div>
          <div class="act"><strong>第二幕：</strong>{{ script.plot_outline.act2 }}</div>
          <div class="act"><strong>第三幕：</strong>{{ script.plot_outline.act3 }}</div>
        </div>
      </section>

      <div class="warning">
        ⚠️ 凶手身份、线索和私信事件将在游戏开始后揭晓
      </div>

      <button @click="$emit('start')" class="start-btn">开始游戏</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { scriptApi } from '@/types/script';
import type { ScriptDetail } from '@/types/script';

const props = defineProps<{ scriptId: string }>();
const emit = defineEmits(['back', 'start']);

const script = ref<ScriptDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    script.value = await scriptApi.getDetail(props.scriptId);
  } catch (e) {
    error.value = '加载剧本失败';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.script-detail { padding: 20px; max-width: 800px; margin: 0 auto; }
.back-btn { background: none; border: none; color: #666; cursor: pointer; margin-bottom: 20px; font-size: 16px; }
.back-btn:hover { color: #333; }
.loading { text-align: center; padding: 40px; color: #666; }
.error { text-align: center; padding: 40px; color: #f44336; }
.content { background: #fff; border-radius: 8px; }
h1 { margin: 0 0 20px 0; color: #333; }
.meta { display: flex; gap: 16px; margin: 20px 0; color: #666; flex-wrap: wrap; }
section { margin: 30px 0; }
h2 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }
.background p { line-height: 1.8; color: #555; }
.role-card { border: 1px solid #eee; padding: 15px; margin: 10px 0; border-radius: 8px; background: #fafafa; }
.role-card h3 { margin: 0 0 10px 0; color: #333; }
.role-card p { margin: 5px 0; color: #666; }
.act { padding: 10px 0; border-bottom: 1px solid #eee; }
.warning { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; color: #856404; }
.start-btn { background: #4caf50; color: white; border: none; padding: 12px 30px; 
             border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 20px; }
.start-btn:hover { background: #45a049; }
</style>
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd client && npm test -- ScriptDetail.spec.ts`
Expected: PASS - all 5 tests pass

- [ ] **Step 3: Run type check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add client/src/components/ScriptDetail.vue
git commit -m "feat: add ScriptDetail component with masked content"
```

---

## Self-Review Checklist

Before marking complete:
- [ ] Component displays script title, metadata, background story
- [ ] Shows role cards with name, age, occupation, description
- [ ] Shows plot outline (act1, act2, act3)
- [ ] Does NOT display true_killer, murder_method, clues, private_events
- [ ] Loading state shown while fetching
- [ ] Error state shown on failure
- [ ] Back button emits 'back' event
- [ ] Start button emits 'start' event
- [ ] Warning message about hidden sensitive info
- [ ] All tests pass
- [ ] TypeScript compilation passes
- [ ] Styling consistent with ScriptList component
