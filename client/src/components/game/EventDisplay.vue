<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';
import { useGameStore } from '../../stores/game';
import { storeToRefs } from 'pinia';

const { currentEvent } = useGameActions();
const store = useGameStore();
const { actBanner } = storeToRefs(store);
</script>

<template>
  <div class="event-display">
    <!-- Act Transition Banner -->
    <div v-if="actBanner" class="act-banner">
      <div class="act-banner-content">
        <span class="act-banner-title">📖 第{{ actBanner.act }}幕开始</span>
        <span v-if="actBanner.plot_summary" class="act-banner-text">{{ actBanner.plot_summary }}</span>
      </div>
    </div>

    <!-- DM Event Display -->
    <div class="event-section">
      <h2>📜 公共事件</h2>
      <div v-if="!currentEvent" class="no-event">等待 DM 发布事件...</div>
      <div v-else class="event-content">{{ currentEvent }}</div>
    </div>
  </div>
</template>

<style scoped>
.event-display {
  margin-bottom: 20px;
}

.act-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  animation: slideDown 0.5s ease;
}

.act-banner-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.act-banner-title {
  font-size: 1.2em;
  font-weight: bold;
}

.act-banner-text {
  font-size: 0.95em;
  opacity: 0.9;
}

.event-section h2 {
  margin-bottom: 12px;
  color: #333;
}

.event-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.no-event {
  color: #999;
  font-style: italic;
  padding: 20px;
  text-align: center;
}

@keyframes slideDown {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
