<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';
import { ref } from 'vue';

const { castVote } = useGameActions();
const voteTarget = ref('');

const submitVote = async () => {
  if (!voteTarget.value) return;
  await castVote(voteTarget.value);
  voteTarget.value = '';
};
</script>

<template>
  <div class="vote-panel">
    <h3>🗳️ 投票指认凶手</h3>
    <select v-model="voteTarget">
      <option value="">选择嫌疑人...</option>
      <!-- Options would come from players list -->
    </select>
    <button @click="submitVote" :disabled="!voteTarget">提交投票</button>
  </div>
</template>

<style scoped>
.vote-panel {
  padding: 10px;
}

h3 {
  margin-bottom: 12px;
}

select {
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 10px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
