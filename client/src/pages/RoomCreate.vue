<template>
  <div class="room-create">
    <h1>创建游戏房间</h1>

    <section class="script-selection">
      <h2>剧本选择（可选）</h2>
      <p class="info">当前支持 LLM 实时生成剧本，无需预设。</p>
      <p class="tip">房间创建后，管理员可在等待大厅选择剧本类型并生成。</p>
    </section>

    <section class="player-info">
      <h2>玩家信息</h2>
      <input 
        v-model="playerName" 
        placeholder="你的名字（主持人）"
        class="player-input"
        maxlength="50"
      />
    </section>

    <button @click="createRoom" :disabled="!playerName" class="create-btn">
      创建房间
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '@/stores/game';

const router = useRouter();
const store = useGameStore();

const playerName = ref('');

function createRoom() {
  if (!playerName.value) return;
  
  // Store admin name
  const adminId = `admin_${Date.now()}`;
  localStorage.setItem(`admin_${adminId}`, playerName.value);
  
  // Create room via API
  store.createRoomWithScript(playerName.value, adminId).then((roomId: string) => {
    router.push(`/lobby/${roomId}`);
  }).catch((err) => {
    console.error('Failed to create room:', err);
    alert('创建房间失败：' + err.message);
  });
}
</script>

<style scoped>
@import '../styles/variables.css';

.room-create {
  max-width: 600px;
  margin: 40px auto;
  padding: var(--space-2xl);
}

h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin-bottom: var(--space-xl);
}

section {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-lg);
}

h2 {
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.info {
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.tip {
  color: var(--accent-primary);
  font-size: 13px;
}

.player-input {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 14px;
}

.create-btn {
  width: 100%;
  padding: var(--space-lg);
  border: none;
  border-radius: var(--radius-lg);
  background: var(--accent-primary);
  color: var(--bg-primary);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.create-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
