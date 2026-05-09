<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';
import { ref } from 'vue';

const { startGame, advanceAct, forceTrial, endGame, phase } = useGameActions();

const adminLoading = ref(false);

const handleStartGame = async () => {
  adminLoading.value = true;
  try {
    await startGame();
  } catch (error) {
    console.error('Failed to start game:', error);
  } finally {
    adminLoading.value = false;
  }
};

const handleAdvanceAct = async () => {
  adminLoading.value = true;
  try {
    await advanceAct();
  } catch (error) {
    console.error('Failed to advance act:', error);
  } finally {
    adminLoading.value = false;
  }
};

const handleForceTrial = async () => {
  adminLoading.value = true;
  try {
    await forceTrial();
  } catch (error) {
    console.error('Failed to force trial:', error);
  } finally {
    adminLoading.value = false;
  }
};

const handleEndGame = async () => {
  adminLoading.value = true;
  try {
    await endGame();
  } catch (error) {
    console.error('Failed to end game:', error);
  } finally {
    adminLoading.value = false;
  }
};
</script>

<template>
  <div class="admin-console">
    <h2>🛠️ 管理员控制台</h2>
    
    <div class="admin-actions">
      <button 
        v-if="phase === 'waiting'" 
        @click="handleStartGame" 
        :disabled="adminLoading"
      >
        {{ adminLoading ? '⏳ 启动中...' : '🎮 启动游戏' }}
      </button>

      <button 
        v-if="phase === 'playing'" 
        @click="handleAdvanceAct" 
        :disabled="adminLoading"
      >
        {{ adminLoading ? '⏳ 推进中...' : '⏭️ 推进到下一幕' }}
      </button>

      <button 
        v-if="phase === 'playing'" 
        @click="handleForceTrial" 
        :disabled="adminLoading"
      >
        {{ adminLoading ? '⏳ 准备中...' : '⚖️ 强制进入审判' }}
      </button>

      <button 
        @click="handleEndGame" 
        :disabled="adminLoading || phase === 'finished'"
      >
        {{ adminLoading ? '⏳ 结束中...' : '🏁 结束游戏' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.admin-console {
  padding: 15px;
  background: #fff3e0;
  border-radius: 8px;
  margin-bottom: 20px;
}

h2 {
  margin-bottom: 15px;
  color: #333;
}

.admin-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

button {
  padding: 12px 16px;
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
}

button:hover:not(:disabled) {
  background: #f57c00;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
