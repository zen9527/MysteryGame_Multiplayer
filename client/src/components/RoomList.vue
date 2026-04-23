<template>
  <div class="room-list">
    <h1>剧本杀</h1>
    <button class="create-btn" @click="createRoom">创建房间</button>
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
const router = useRouter();

async function createRoom() {
  const creatorId = `admin_${Date.now()}`;
  localStorage.setItem('player_id', creatorId);
  const res = await fetch('/api/rooms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ creator_id: creatorId }),
  });
  const data = await res.json();
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
}

.create-btn:hover {
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
