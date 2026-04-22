<template>
  <div class="waiting-lobby">
    <h1>等待其他玩家加入</h1>
    <p class="room-id">房间: {{ gameId }}</p>
    <div class="player-list">
      <div v-for="(player, pid) in players" :key="pid" class="player-card">
        <span class="player-name">{{ player.name }}</span>
        <span v-if="player.role_id" class="role-badge">角色 #{{ player.role_id.slice(-4) }}</span>
      </div>
    </div>
    <p class="count">{{ playerCount }} / {{ maxPlayers }} 玩家</p>
    <button @click="startGame" :disabled="!canStart || starting">
      {{ starting ? '开始中...' : '开始游戏' }}
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

const gameId = route.params.gameId as string;

const players = ref<Record<string, { name: string; role_id: string }>>({});
const maxPlayers = ref(6);
const canStart = computed(() => playerCount.value >= 2);
const starting = ref(false);
const error = ref('');

const playerCount = computed(() => Object.keys(players.value).length);

async function fetchState() {
  try {
    const res = await fetch(`/api/rooms/${gameId}`);
    if (!res.ok) return;
    const data = await res.json();
    players.value = data.players || {};
    maxPlayers.value = Object.keys(players.value).length + 2; // estimate
  } catch {
    // silently ignore
  }
}

async function startGame() {
  if (!canStart.value || starting.value) return;
  starting.value = true;
  error.value = '';
  try {
    const res = await fetch(`/api/rooms/${gameId}/start`, { method: 'POST' });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '开始失败');
    }
    // Navigate to game page
    router.push(`/game/${gameId}`);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    starting.value = false;
  }
}

onMounted(() => {
  fetchState();
  // Poll every 3 seconds for player updates
  const interval = setInterval(fetchState, 3000);
  return () => clearInterval(interval);
});
</script>

<style scoped>
.waiting-lobby {
  max-width: 500px;
  margin: 40px auto;
  text-align: center;
}
.room-id {
  color: #888;
  margin-bottom: 24px;
}
.player-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 20px 0;
}
.player-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #16213e;
  border-radius: 6px;
}
.player-name {
  font-size: 16px;
}
.role-badge {
  font-size: 12px;
  color: #e94560;
}
.count {
  color: #aaa;
  margin-bottom: 20px;
}
button {
  padding: 12px 32px;
  border: none;
  border-radius: 6px;
  background: #0f3460;
  color: #eee;
  font-size: 16px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
button:hover:not(:disabled) {
  background: #e94560;
}
.error {
  color: #e94560;
  margin-top: 12px;
}
</style>
