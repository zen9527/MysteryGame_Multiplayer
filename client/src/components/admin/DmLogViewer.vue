<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';

const { privateMessages } = useGameActions();
</script>

<template>
  <div class="dm-log-viewer">
    <h2>🎭 DM 聊天记录</h2>
    <div class="log-content">
      <div 
        v-for="(msg, i) in privateMessages" 
        :key="i" 
        class="log-entry"
      >
        <span class="sender">{{ msg.from }}</span>
        <span class="text">{{ msg.content }}</span>
        <span class="timestamp">{{ msg.timestamp }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dm-log-viewer {
  padding: 15px;
}

h2 {
  margin-bottom: 12px;
}

.log-content {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.log-entry {
  margin-bottom: 10px;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.sender {
  font-weight: bold;
  color: #555;
  margin-right: 8px;
}

.text {
  color: #333;
}

.timestamp {
  float: right;
  font-size: 0.8em;
  color: #999;
}
</style>
