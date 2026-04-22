<template>
  <div class="game-timer">
    <span>{{ remainingMinutes }}:{{ remainingSeconds.toString().padStart(2, '0') }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const remainingMinutes = ref(60);
const remainingSeconds = ref(0);
let interval: number | null = null;

onMounted(() => {
  interval = window.setInterval(() => {
    if (remainingSeconds.value > 0) {
      remainingSeconds.value--;
    } else if (remainingMinutes.value > 0) {
      remainingMinutes.value--;
      remainingSeconds.value = 59;
    }
  }, 1000);
});

onUnmounted(() => {
  if (interval) clearInterval(interval);
});
</script>
