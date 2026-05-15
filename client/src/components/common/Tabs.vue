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
