<template>
  <div class="room-join">
    <h1>加入房间</h1>
    <input v-model="playerName" placeholder="输入你的名字" />
    <button @click="join" :disabled="!playerName || joining">
      {{ joining ? '加入中...' : '加入游戏' }}
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();
const playerName = ref('');
const joining = ref(false);
const error = ref('');

async function join() {
  if (!playerName.value) return;
  joining.value = true;
  error.value = '';
  const gameId = route.params.gameId as string;
  const playerId = `player_${Date.now()}`;

  try {
    const res = await fetch(`/api/rooms/${gameId}/players`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, name: playerName.value }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '加入失败');
    }
    const data = await res.json();
    // Save player_id for later use
    localStorage.setItem('player_id', data.player_id);
    // Navigate to lobby with player info
    router.push(`/lobby/${gameId}?player_id=${data.player_id}&role_id=${data.role_id}`);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    joining.value = false;
  }
}
</script>

<style scoped>
.room-join {
  max-width: 400px;
  margin: 60px auto;
  text-align: center;
}
.room-join input {
  display: block;
  width: 100%;
  padding: 12px;
  margin: 16px 0;
  border: 1px solid #444;
  border-radius: 6px;
  background: #16213e;
  color: #eee;
  font-size: 16px;
}
.room-join button {
  padding: 12px 32px;
  border: none;
  border-radius: 6px;
  background: #0f3460;
  color: #eee;
  font-size: 16px;
  cursor: pointer;
}
.room-join button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.room-join button:hover:not(:disabled) {
  background: #e94560;
}
.error {
  color: #e94560;
  margin-top: 12px;
}
</style>
