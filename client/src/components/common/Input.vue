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
  if (val !== undefined) {
    emit('update:modelValue', val);
  }
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
