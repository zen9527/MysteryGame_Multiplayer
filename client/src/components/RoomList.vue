<template>
  <div class="room-list">
    <h1>剧本杀</h1>
    <button @click="createRoom">创建房间</button>
    <div v-if="rooms.length > 0">
      <h2>现有房间</h2>
      <div v-for="room in rooms" :key="room.game_id">
        <span>{{ room.game_id }} - {{ room.player_count }} 玩家</span>
        <button @click="joinRoom(room.game_id)">加入</button>
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
  const res = await fetch('/api/rooms', { method: 'POST' });
  const data = await res.json();
  router.push(`/join/${data.game_id}`);
}

async function joinRoom(gameId: string) {
  router.push(`/join/${gameId}`);
}

onMounted(async () => {
  const res = await fetch('/api/rooms');
  rooms.value = await res.json();
});
</script>
