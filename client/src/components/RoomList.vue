<template>
  <div class="room-list">
    <h1>剧本杀</h1>
    <div class="create-section">
      <input v-model="creatorName" placeholder="输入你的名字" @keyup.enter="createRoom" />
      <button class="create-btn" @click="createRoom" :disabled="!creatorName.trim()">创建房间</button>
    </div>
    <div v-if="rooms.length > 0" class="rooms-section">
      <h2>现有房间</h2>
      <div v-for="room in rooms" :key="room.game_id || room.id" class="room-card">
        <span>{{ room.game_id || room.id }}</span>
        <span class="player-count">{{ room.player_count || 0 }} 玩家</span>
        <button @click="joinRoom(room.game_id || room.id)">加入</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const rooms = ref<any[]>([]);
const creatorName = ref('');
const router = useRouter();

async function createRoom() {
  if (!creatorName.value.trim()) return;
  const creatorId = `admin_${Date.now()}`;
  const res = await fetch('/api/rooms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ creator_id: creatorId, name: creatorName.value.trim() }),
  });
  const data = await res.json();
  // Store admin ID with room association
  localStorage.setItem(`admin_${data.game_id}`, creatorId);
  router.push(`/lobby/${data.game_id}`); // Go directly to lobby as admin
}

async function joinRoom(gameId: string) {
  console.log('Joining room:', gameId);
  router.push(`/join/${gameId}`);
}

onMounted(async () => {
  try {
    const res = await fetch('/api/rooms');
    const data = await res.json();
    console.log('Rooms loaded:', data);
    rooms.value = data;
  } catch (e) {
    console.error('Failed to load rooms:', e);
  }
});
</script>

<style scoped>
.room-list {
  max-width: 600px;
  margin: 40px auto;
  text-align: center;
}

h1 {
  font-size: 32px;
  margin-bottom: 32px;
  color: #eee;
}

.create-section {
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;
}
.create-section input {
  padding: 12px 16px;
  border: 1px solid #444;
  border-radius: 8px;
  background: #16213e;
  color: #eee;
  font-size: 16px;
  width: 220px;
}
.create-section input::placeholder { color: #555; }

.create-btn {
  padding: 16px 48px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  white-space: nowrap;
}
.create-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
}

.rooms-section {
  margin-top: 48px;
}

h2 {
  font-size: 20px;
  color: #aaa;
  margin-bottom: 24px;
}

.room-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 12px;
}

.room-card span:first-child {
  font-family: monospace;
  color: #888;
  font-size: 14px;
}

.player-count {
  color: #aaa;
  font-size: 14px;
}

.room-card button {
  padding: 8px 24px;
  border: none;
  border-radius: 6px;
  background: #0f3460;
  color: #eee;
  cursor: pointer;
}

.room-card button:hover {
  background: #e94560;
}
</style>
