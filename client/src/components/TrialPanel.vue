<template>
  <div class="trial-panel">
    <h1>审判环节</h1>
    <div v-for="accusation in accusations" :key="accusation.id">
      <strong>{{ accusation.from }}</strong> 指控 <strong>{{ accusation.target }}</strong>
      <p>{{ accusation.reasoning }}</p>
    </div>
    <div class="vote-results">
      <h2>投票结果</h2>
      <div v-for="(count, name) in results" :key="name">
        {{ name }}: {{ count }} 票
      </div>
      <p v-if="consensus">达成共识！</p>
      <p v-else>未达成共识，继续游戏</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const accusations = ref<any[]>([]);
const results = ref<Record<string, number>>({});
const consensus = ref(false);
</script>
