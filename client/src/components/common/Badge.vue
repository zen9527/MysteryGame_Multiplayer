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
