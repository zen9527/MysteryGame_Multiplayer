<template>
  <div class="accusation-panel">
    <h2>指控</h2>
    <select v-model="target">
      <option v-for="player in players" :key="player.id" :value="player.name">
        {{ player.name }}
      </option>
    </select>
    <textarea v-model="reasoning" placeholder="写下你的推理..."></textarea>
    <button @click="accuse">提出指控</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const target = ref('');
const reasoning = ref('');
const players = ref<any[]>([]);

function accuse() {
  // 发送指控
}
</script>
