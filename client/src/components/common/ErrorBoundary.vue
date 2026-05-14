<template>
  <div v-if="error" class="error-boundary">
    <h3>⚠️ {{ title }}</h3>
    <p>{{ error.message }}</p>
    <button @click="handleRetry">🔄 Retry</button>
    <button @click="$emit('dismiss')">Dismiss</button>
  </div>
  <slot v-else></slot>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  title?: string;
  onRetry?: () => Promise<void>;
}>();

defineEmits(['dismiss']);

const error = ref<Error | null>(null);

async function handleRetry() {
  if (props.onRetry) {
    try {
      await props.onRetry();
      error.value = null;
    } catch (e) {
      error.value = e as Error;
    }
  }
}

function setError(err: Error) {
  error.value = err;
}

defineExpose({ error, setError });
</script>

<style scoped>
.error-boundary {
  padding: var(--space-xl);
  background: rgba(233, 69, 96, 0.1);
  border: 1px solid rgba(233, 69, 96, 0.3);
  border-radius: var(--radius-md);
  text-align: center;
}

.error-boundary h3 {
  color: #e94560;
  margin-bottom: var(--space-md);
}

.error-boundary p {
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
}

button {
  margin: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  cursor: pointer;
  background: var(--bg-secondary);
  border: 1px solid var(--border-medium);
  color: var(--text-primary);
}

button:hover {
  background: var(--hover-bg);
}
</style>
