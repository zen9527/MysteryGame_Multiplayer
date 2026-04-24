<template>
  <div class="game-timer">
    <span v-if="totalSeconds > 0">{{ minutes }}:{{ seconds.toString().padStart(2, '0') }}</span>
    <span v-else class="timed-out">时间到！</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';

const props = defineProps<{
  totalSeconds: number;
}>();

const remainingSeconds = ref(props.totalSeconds);
let interval: number | null = null;

onMounted(() => {
  interval = window.setInterval(() => {
    if (remainingSeconds.value > 0) {
      remainingSeconds.value--;
    }
  }, 1000);
});

watch(() => props.totalSeconds, (val) => {
  remainingSeconds.value = val;
});

onUnmounted(() => {
  if (interval) clearInterval(interval);
});

const minutes = computed(() => Math.floor(remainingSeconds.value / 60));
const seconds = computed(() => remainingSeconds.value % 60);
const totalSeconds = computed(() => props.totalSeconds);
</script>

<style scoped>
.game-timer {
  font-family: monospace;
  font-size: 18px;
  color: #eee;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
}
.timed-out {
  color: #e94560;
  font-weight: bold;
}
</style>
