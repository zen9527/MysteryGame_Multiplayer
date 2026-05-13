# UI Design System & Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the midnight purple-blue design system foundation and collapsible sidebar navigation

**Architecture:** Create CSS custom properties for global theming, build reusable component library, implement collapsible sidebar with hover expansion (80px → 240px)

**Tech Stack:** Vue 3, CSS custom properties, TypeScript

---

## File Structure

```
client/src/
  styles/
    variables.css          # CSS custom properties (create)
    global.css             # Global resets + base styles (create)
  components/
    common/
      CollapsibleSidebar.vue   # Create
      Button.vue               # Create
      Input.vue                # Create
      Card.vue                 # Create
      Badge.vue                # Create
      Tabs.vue                 # Create
  App.vue                      # Modify - update base styles
  router.ts                    # Modify - add layout wrapper
```

---

### Task 1: Create CSS Design System Variables

**Files:**
- Create: `client/src/styles/variables.css`

- [ ] **Step 1: Write the CSS custom properties**

```css
/* client/src/styles/variables.css */

:root {
  /* Backgrounds - Midnight Purple Blue */
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-tertiary: #0f0f23;
  
  /* Accents */
  --accent-primary: #79c0ff;    /* Blue - primary actions */
  --accent-secondary: #d2a8ff;  /* Purple - secondary accents */
  
  /* Text Colors */
  --text-primary: #c9d6df;      /* Main text */
  --text-secondary: #8b949e;    /* Secondary text */
  --text-muted: #666;           /* Muted/disabled text */
  
  /* Border Colors */
  --border-light: rgba(255, 255, 255, 0.05);
  --border-medium: rgba(255, 255, 255, 0.1);
  --border-accent: rgba(121, 192, 255, 0.3);
  
  /* Interactive States */
  --hover-bg: rgba(255, 255, 255, 0.05);
  --active-bg: rgba(121, 192, 255, 0.15);
  --focus-border: rgba(121, 192, 255, 0.4);
  
  /* Spacing Scale */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 20px;
  --space-2xl: 24px;
  --space-3xl: 32px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-round: 50%;
  
  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'SF Mono', 'Courier New', monospace;
  
  /* Transitions */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Shadows (Flat Design - Minimal) */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
}
```

- [ ] **Step 2: Commit**

```bash
git add client/src/styles/variables.css
git commit -m "style: add CSS custom properties for midnight purple-blue design system"
```

---

### Task 2: Create Global Styles

**Files:**
- Create: `client/src/styles/global.css`
- Modify: `client/main.ts` (add import)

- [ ] **Step 1: Write global reset and base styles**

```css
/* client/src/styles/global.css */

@import './variables.css';

/* Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Base Styles */
html, body {
  height: 100%;
  font-family: var(--font-family);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Focus Styles */
:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

/* Link Styles */
a {
  color: var(--accent-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--accent-secondary);
}

/* Button Reset */
button {
  font-family: inherit;
  cursor: pointer;
}

/* Input Reset */
input, textarea {
  font-family: inherit;
}
```

- [ ] **Step 2: Import global styles in main.ts**

```typescript
// client/src/main.ts
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import './styles/global.css'; // Add this line

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');
```

- [ ] **Step 3: Test build**

```bash
cd client && npm run build
```

Expected: Build succeeds without errors

- [ ] **Step 4: Commit**

```bash
git add client/src/styles/global.css client/src/main.ts
git commit -m "style: add global styles and import design system variables"
```

---

### Task 3: Create CollapsibleSidebar Component

**Files:**
- Create: `client/src/components/common/CollapsibleSidebar.vue`
- Modify: `client/src/App.vue` (use the sidebar)

- [ ] **Step 1: Write the component**

```vue
<!-- client/src/components/common/CollapsibleSidebar.vue -->
<template>
  <aside class="collapsible-sidebar">
    <div class="logo-section">
      <div class="logo">🎭</div>
    </div>
    
    <nav class="nav-section">
      <div 
        v-for="item in navItems" 
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="navigate(item.path)"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="text">{{ item.label }}</span>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

interface NavItem {
  icon: string;
  label: string;
  path: string;
}

const navItems = computed<NavItem[]>(() => [
  { icon: '🏠', label: '房间列表', path: '/' },
  { icon: '📚', label: '剧本中心', path: '/scripts' },
  { icon: '⚙️', label: 'LLM 配置', path: '/settings' }
]);

function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/');
}

function navigate(path: string): void {
  router.push(path);
}
</script>

<style scoped>
@import '../../styles/variables.css';

.collapsible-sidebar {
  width: 80px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-light);
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: var(--space-xl) 0;
  transition: width var(--transition-normal);
  overflow: hidden;
  position: fixed;
  left: 0;
  top: 0;
}

.collapsible-sidebar:hover {
  width: 240px;
}

.logo-section {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-3xl);
}

.logo {
  font-size: 28px;
  filter: drop-shadow(0 0 10px rgba(121, 192, 255, 0.5));
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: 0 var(--space-lg);
}

.nav-item {
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--active-bg);
  color: var(--accent-primary);
}

.nav-item .icon {
  font-size: 20px;
  margin-right: var(--space-lg);
  min-width: 28px;
}

.nav-item .text {
  opacity: 0;
  transition: opacity var(--transition-fast);
  font-weight: 500;
  font-size: 13px;
}

.collapsible-sidebar:hover .nav-item .text {
  opacity: 1;
}
</style>
```

- [ ] **Step 2: Update App.vue to use sidebar**

```vue
<!-- client/src/App.vue -->
<template>
  <div id="app">
    <CollapsibleSidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import CollapsibleSidebar from './components/common/CollapsibleSidebar.vue';
</script>

<style>
@import './styles/variables.css';

#app {
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: 80px;
  flex: 1;
  background: var(--bg-tertiary);
  min-height: 100vh;
}
</style>
```

- [ ] **Step 3: Test in browser**

```bash
cd client && npm run dev
```

Open http://localhost:3000, verify sidebar collapses/expands on hover

- [ ] **Step 4: Commit**

```bash
git add client/src/components/common/CollapsibleSidebar.vue client/src/App.vue
git commit -m "feat: add collapsible sidebar navigation with hover expansion"
```

---

### Task 4: Create Button Component

**Files:**
- Create: `client/src/components/common/Button.vue`

- [ ] **Step 1: Write the component**

```vue
<!-- client/src/components/common/Button.vue -->
<template>
  <button 
    class="btn"
    :class="[variant, size, { disabled: disabled, loading }]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="spinner"></span>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
}>();

defineEmits<{
  click: [event: MouseEvent];
}>();
</script>

<style scoped>
@import '../../styles/variables.css';

.btn {
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Variants */
.btn-primary {
  background: var(--accent-primary);
  color: var(--bg-primary);
}

.btn-primary:hover:not(:disabled) {
  background: #5fa8e8;
}

.btn-secondary {
  background: var(--hover-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-medium);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--active-bg);
  border-color: var(--accent-primary);
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--hover-bg);
  color: var(--text-primary);
}

/* Sizes */
.btn-sm {
  padding: var(--space-sm) var(--space-md);
  font-size: 12px;
}

.btn-md {
  padding: var(--space-md) var(--space-lg);
  font-size: 14px;
}

.btn-lg {
  padding: var(--space-lg) var(--space-xl);
  font-size: 16px;
}

/* Spinner */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add client/src/components/common/Button.vue
git commit -m "feat: add Button component with variants and sizes"
```

---

### Task 5: Create Input Component

**Files:**
- Create: `client/src/components/common/Input.vue`

- [ ] **Step 1: Write the component**

```vue
<!-- client/src/components/common/Input.vue -->
<template>
  <div class="input-wrapper">
    <label v-if="label" class="label">{{ label }}</label>
    <input
      v-model="internalValue"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="{ error }"
      class="input"
      @focus="$emit('focus', $event)"
      @blur="$emit('blur', $event)"
    />
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  modelValue?: string | number;
  type?: 'text' | 'email' | 'password' | 'number';
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string | number];
  focus: [event: FocusEvent];
  blur: [event: FocusEvent];
}>();

const internalValue = ref(props.modelValue);

watch(() => props.modelValue, (val) => {
  internalValue.value = val;
});

watch(internalValue, (val) => {
  emit('update:modelValue', val);
});
</script>

<style scoped>
@import '../../styles/variables.css';

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.input {
  padding: var(--space-md) var(--space-lg);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 14px;
  transition: all var(--transition-fast);
}

.input::placeholder {
  color: var(--text-muted);
}

.input:hover:not(:disabled) {
  border-color: var(--border-medium);
}

.input:focus {
  outline: none;
  border-color: var(--focus-border);
  background: rgba(255, 255, 255, 0.06);
}

.input.error {
  border-color: #ef4444;
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  font-size: 11px;
  color: #ef4444;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add client/src/components/common/Input.vue
git commit -m "feat: add Input component with validation support"
```

---

### Task 6: Create Card, Badge, Tabs Components

**Files:**
- Create: `client/src/components/common/Card.vue`
- Create: `client/src/components/common/Badge.vue`
- Create: `client/src/components/common/Tabs.vue`

- [ ] **Step 1: Write Card component**

```vue
<!-- client/src/components/common/Card.vue -->
<template>
  <div class="card" :class="{ hoverable }">
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  hoverable?: boolean;
}>();
</script>

<style scoped>
@import '../../styles/variables.css';

.card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.card.hoverable {
  transition: all var(--transition-fast);
}

.card.hoverable:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--border-accent);
}
</style>
```

- [ ] **Step 2: Write Badge component**

```vue
<!-- client/src/components/common/Badge.vue -->
<template>
  <span class="badge" :class="[variant, size]">
    <slot></slot>
  </span>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'default' | 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md';
}>();
</script>

<style scoped>
@import '../../styles/variables.css';

.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
}

.badge-default {
  background: var(--hover-bg);
  color: var(--text-secondary);
}

.badge-primary {
  background: rgba(121, 192, 255, 0.15);
  color: var(--accent-primary);
}

.badge-secondary {
  background: rgba(210, 168, 255, 0.15);
  color: var(--accent-secondary);
}

.badge-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.badge-sm {
  padding: 2px var(--space-sm);
  font-size: 10px;
}

.badge-md {
  padding: var(--space-xs) var(--space-md);
  font-size: 11px;
}
</style>
```

- [ ] **Step 3: Write Tabs component**

```vue
<!-- client/src/components/common/Tabs.vue -->
<template>
  <div class="tabs-container">
    <div class="tabs-header">
      <button
        v-for="(tab, index) in tabs"
        :key="index"
        class="tab"
        :class="{ active: modelValue === index }"
        @click="$emit('update:modelValue', index)"
      >
        {{ tab }}
      </button>
    </div>
    <div class="tabs-content">
      <slot :active="modelValue"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tabs: string[];
  modelValue: number;
}>();

defineEmits<{
  'update:modelValue': [index: number];
}>();
</script>

<style scoped>
@import '../../styles/variables.css';

.tabs-container {
  display: flex;
  flex-direction: column;
}

.tabs-header {
  display: flex;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid var(--border-light);
}

.tab {
  flex: 1;
  padding: var(--space-md);
  text-align: center;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  transition: all var(--transition-fast);
  border-bottom: 2px solid transparent;
  background: transparent;
  border: none;
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
  background: rgba(121, 192, 255, 0.05);
}

.tabs-content {
  flex: 1;
}
</style>
```

- [ ] **Step 4: Test build**

```bash
cd client && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add client/src/components/common/Card.vue client/src/components/common/Badge.vue client/src/components/common/Tabs.vue
git commit -m "feat: add Card, Badge, and Tabs components"
```

---

## Self-Review Checklist

✅ **Spec coverage:** All design system variables, global styles, and core navigation components implemented

✅ **Placeholder scan:** No TBD/TODO placeholders found

✅ **Type consistency:** All component props/emits properly typed with TypeScript

✅ **File paths:** All exact paths provided

✅ **Code completeness:** Every step includes actual code blocks

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-12-ui-design-system-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
