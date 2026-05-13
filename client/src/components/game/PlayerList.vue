<template>
  <div class="player-list">
    <div 
      v-for="player in players" 
      :key="player.id"
      class="player-card"
    >
      <div class="player-header">
        <span class="player-name">{{ player.name }}</span>
        <div class="player-status" :class="{ idle: isIdle(player) }"></div>
      </div>
      <div class="player-role">{{ player.roleName }} · {{ player.roleTitle }}</div>
      <div class="player-info">
        <span>角色卡：Layer {{ player.layer }}</span>
        <span>{{ formatTime(player.onlineTime) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Player {
  id: string;
  name: string;
  roleName: string;
  roleTitle: string;
  layer: number;
  onlineTime: number;
  lastActivity: number;
}

defineProps<{
  players: Player[];
}>();

function isIdle(player: Player): boolean {
  return Date.now() - player.lastActivity > 60000;
}

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  if (hrs > 0) return `${hrs}h ${mins % 60}m`;
  return `${mins}m`;
}
</script>

<style scoped>
@import '../../styles/variables.css';

.player-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.player-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  border: 1px solid var(--border-light);
  transition: all var(--transition-fast);
}

.player-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--border-accent);
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.player-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.player-status {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-round);
  background: #10b981;
}

.player-status.idle {
  background: #f59e0b;
}

.player-role {
  font-size: 11px;
  color: var(--accent-primary);
  margin-bottom: var(--space-xs);
}

.player-info {
  font-size: 10px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
}
</style>
