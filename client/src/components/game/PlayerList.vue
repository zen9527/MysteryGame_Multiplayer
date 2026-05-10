<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';

const { players } = useGameActions();
</script>

<template>
  <div class="player-list">
    <h2>👥 玩家列表 ({{ players.size }})</h2>
    <div v-for="[pid, player] in players" :key="pid" class="player-item">
      <span class="player-name">{{ player.name }}</span>
      <span v-if="player.role_id" class="role-tag">角色：{{ player.role_id }}</span>
      <span v-if="player.role_id === 'admin'" class="admin-tag">👑</span>
    </div>
  </div>
</template>

<style scoped>
.player-list {
  padding: 10px;
}

h2 {
  margin-bottom: 12px;
  color: #333;
}

.player-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.player-name {
  font-weight: bold;
  color: #555;
}

.role-tag {
  background: #667eea;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.85em;
}

.admin-tag {
  font-size: 1.2em;
}
</style>
