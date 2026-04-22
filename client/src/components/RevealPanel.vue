<template>
  <div class="reveal-panel">
    <h1>真相揭晓</h1>
    <div class="truth">
      <h2>真凶</h2>
      <p>{{ truth.killer }}</p>
      <h2>作案手法</h2>
      <p>{{ truth.method }}</p>
      <h2>完整复盘</h2>
      <p>{{ truth.story }}</p>
    </div>
    <div class="evaluations">
      <h2>玩家评价</h2>
      <div v-for="(evaluation, name) in evaluations" :key="name">
        <strong>{{ name }}</strong>: {{ evaluation }}
      </div>
    </div>
    <button @click="backToRoom">返回房间列表</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const truth = ref({ killer: '', method: '', story: '' });
const evaluations = ref<Record<string, string>>({});

function backToRoom() {
  // 返回房间列表
}
</script>
