<!-- client/src/components/game/EventBanner.vue -->
<template>
  <div class="event-banner">
    <div class="act-indicator">ACT {{ act }}</div>
    <div class="event-title">{{ title }}</div>
    <div class="event-content">{{ content }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  act: number;
  title: string;
  content: string;
}>();
</script>

<style scoped>
@import '../../styles/variables.css';

.event-banner {
  background: rgba(210, 168, 255, 0.1);
  border-bottom: 1px solid rgba(210, 168, 255, 0.2);
  padding: var(--space-lg) var(--space-xl);
  flex-shrink: 0;
}

.act-indicator {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(210, 168, 255, 0.2);
  border-radius: var(--radius-sm);
  font-size: 10px;
  color: var(--accent-secondary);
  margin-bottom: var(--space-sm);
  font-weight: 600;
}

.event-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-secondary);
  margin-bottom: var(--space-xs);
}

.event-content {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}
</style>
