<template>
  <div class="vote-panel">
    <h2>投票</h2>
    <select v-model="target">
      <option v-for="player in players" :key="player.id" :value="player.name">
        {{ player.name }}
      </option>
    </select>
    <textarea v-model="reasoning" placeholder="投票理由..."></textarea>
    <button @click="vote">投票</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const target = ref('');
const reasoning = ref('');
const players = ref<any[]>([]);

function vote() {
  // 发送投票
}
</script>
