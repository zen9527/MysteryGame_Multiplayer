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
