<template>
  <div class="clock-container">
    <div class="analog-clock">
      <div class="clock-center"></div>
      <div 
        v-for="mark in 12" 
        :key="mark" 
        class="hour-mark" 
        :class="{ major: mark % 3 === 0 }"
        :style="{ transform: `rotate(${mark * 30}deg)` }"
      ></div>
      <div class="hand hour" :style="{ transform: `rotate(${hourDeg}deg)` }"></div>
      <div class="hand minute" :style="{ transform: `rotate(${minuteDeg}deg)` }"></div>
      <div class="hand second" :style="{ transform: `rotate(${secondDeg}deg)` }"></div>
    </div>
    <div class="digital-time">{{ digitalTime }}</div>
    <div class="clock-label">游戏进行中</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const hourDeg = ref(0);
const minuteDeg = ref(0);
const secondDeg = ref(0);
const digitalTime = ref('');

let timer: number | null = null;

function updateClock() {
  const now = new Date();
  hourDeg.value = (now.getHours() % 12) * 30 + now.getMinutes() * 0.5;
  minuteDeg.value = now.getMinutes() * 6 + now.getSeconds() * 0.1;
  secondDeg.value = now.getSeconds() * 6;
  digitalTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
}

onMounted(() => {
  updateClock();
  timer = window.setInterval(updateClock, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
@import '../../styles/variables.css';

.clock-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--space-3xl);
}

.analog-clock {
  width: 180px;
  height: 180px;
  border: 4px solid var(--accent-primary);
  border-radius: var(--radius-round);
  position: relative;
  background: var(--bg-secondary);
}

.clock-center {
  width: 12px;
  height: 12px;
  background: var(--accent-primary);
  border-radius: var(--radius-round);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.hour-mark {
  position: absolute;
  width: 2px;
  height: 12px;
  background: var(--text-secondary);
  top: 8px;
  left: 50%;
  transform-origin: center 86px;
}

.hour-mark.major {
  width: 3px;
  height: 16px;
  background: var(--accent-primary);
}

.hand {
  position: absolute;
  bottom: 50%;
  left: 50%;
  transform-origin: bottom center;
  border-radius: 2px;
}

.hour {
  width: 4px;
  height: 45px;
  background: var(--text-primary);
  margin-left: -2px;
}

.minute {
  width: 3px;
  height: 65px;
  background: var(--accent-primary);
  margin-left: -1.5px;
}

.second {
  width: 2px;
  height: 70px;
  background: var(--accent-secondary);
  margin-left: -1px;
}

.digital-time {
  margin-top: var(--space-lg);
  font-size: 24px;
  font-weight: 600;
  color: var(--accent-primary);
  font-family: var(--font-mono);
}

.clock-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: var(--space-xs);
}
</style>
