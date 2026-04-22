<template>
  <div class="event-display">
    <h2>当前事件</h2>
    <p>{{ currentEvent }}</p>
    <div v-if="isThinking" class="thinking">
      主持人正在思考...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const currentEvent = ref('');
const isThinking = ref(false);
</script>
