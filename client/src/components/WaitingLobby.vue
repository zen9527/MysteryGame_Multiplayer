<template>
  <div class="waiting-lobby">
    <h1>等待其他玩家</h1>
    <div v-for="player in players" :key="player.id">
      {{ player.name }} - {{ player.role_name }}
    </div>
    <button @click="startGame" v-if="allReady">开始游戏</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const players = ref<any[]>([]);
const allReady = computed(() => players.value.length >= 2);

function startGame() {
  // 触发游戏开始
}
</script>
