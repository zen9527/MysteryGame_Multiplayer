<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';
import { ref } from 'vue';

const { submitAccusation } = useGameActions();
const showAccusation = ref(false);
const accusationTarget = ref('');
const accusationReasoning = ref('');

const submitAccus = async () => {
  if (!accusationTarget.value || !accusationReasoning.value) return;
  await submitAccusation(accusationTarget.value, accusationReasoning.value);
  showAccusation.value = false;
  accusationTarget.value = '';
  accusationReasoning.value = '';
};
</script>

<template>
  <div class="accusation-panel">
    <button v-if="!showAccusation" @click="showAccusation = true">开始指控</button>
    
    <div v-if="showAccusation" class="accusation-form">
      <h3>🔍 提交指控</h3>
      <select v-model="accusationTarget">
        <option value="">选择嫌疑人...</option>
        <!-- Options would come from players list -->
      </select>
      <textarea v-model="accusationReasoning" placeholder="说明你的推理..."></textarea>
      <div class="form-actions">
        <button @click="submitAccus">提交</button>
        <button @click="showAccusation = false">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.accusation-panel {
  padding: 10px;
}

button {
  padding: 8px 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.accusation-form {
  background: #fff3e0;
  padding: 15px;
  border-radius: 6px;
  margin-top: 10px;
}

h3 {
  margin-bottom: 12px;
}

select, textarea {
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

textarea {
  min-height: 80px;
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 8px;
}

.form-actions button:last-child {
  background: #9e9e9e;
}
</style>
