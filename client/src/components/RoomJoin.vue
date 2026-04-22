<template>
  <div class="room-join">
    <h1>加入房间</h1>
    <input v-model="playerName" placeholder="输入你的名字" />
    <button @click="join" :disabled="!playerName">加入游戏</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();
const playerName = ref('');

function join() {
  const roomId = route.params.roomId as string;
  router.push(`/lobby/${roomId}?name=${playerName.value}`);
}
</script>
