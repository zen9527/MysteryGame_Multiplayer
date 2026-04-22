<template>
  <div class="game-page">
    <!-- Header -->
    <header class="game-header">
      <h1>{{ script.title || '剧本杀' }}</h1>
      <span class="phase-badge">{{ phaseText }}</span>
      <GameTimer />
    </header>

    <!-- Main content -->
    <div class="game-body">
      <!-- Left: Event display + Chat -->
      <div class="main-panel">
        <!-- DM Event Display -->
        <div class="event-section">
          <h2>📜 当前事件</h2>
          <div v-if="currentEvent" class="event-content">{{ currentEvent }}</div>
          <div v-else class="no-event">等待主持人发布任务...</div>
        </div>

        <!-- Chat Panel -->
        <div class="chat-section">
          <h2>💬 聊天</h2>
          <div class="messages" ref="messageContainer">
            <div v-for="(msg, i) in messages" :key="i" class="message-item">
              <span class="sender">{{ msg.from }}</span>
              <span class="text">{{ msg.content }}</span>
            </div>
          </div>
          <div class="chat-input-row">
            <input v-model="newMessage" @keyup.enter="sendMessage" placeholder="输入消息..." />
            <button @click="sendMessage">发送</button>
          </div>
        </div>
      </div>

      <!-- Right: Players + Actions -->
      <aside class="side-panel">
        <!-- Player List -->
        <div class="players-section">
          <h2>👥 玩家 ({{ playerCount }})</h2>
          <div v-for="(player, pid) in players" :key="pid" class="player-item">
            <span>{{ player.name }}</span>
            <span class="role-tag">#{{ player.role_id.slice(-4) }}</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="actions-section">
          <h2>⚡ 操作</h2>
          <button @click="requestClue" :disabled="phase !== 'playing'">请求线索</button>
          <button @click="startAccusation" :disabled="phase !== 'playing'">开始指控</button>
        </div>

        <!-- Accusation Panel -->
        <div v-if="showAccusation" class="accusation-section">
          <h2>🔍 指控凶手</h2>
          <select v-model="targetRole">
            <option value="">选择目标...</option>
            <option v-for="(player, pid) in players" :key="pid" :value="player.role_id">
              {{ player.name }} (角色 #{{ player.role_id.slice(-4) }})
            </option>
          </select>
          <textarea v-model="reasoning" placeholder="写下你的推理..."></textarea>
          <div class="accusation-buttons">
            <button @click="submitAccusation" :disabled="!targetRole || !reasoning">提交指控</button>
            <button @click="showAccusation = false" class="cancel-btn">取消</button>
          </div>
        </div>

        <!-- Vote Panel -->
        <div v-if="phase === 'trial'" class="vote-section">
          <h2>🗳️ 投票环节</h2>
          <select v-model="voteTarget">
            <option value="">选择目标...</option>
            <option v-for="(player, pid) in players" :key="pid" :value="player.role_id">
              {{ player.name }} (角色 #{{ player.role_id.slice(-4) }})
            </option>
          </select>
          <textarea v-model="voteReasoning" placeholder="写下你的推理..."></textarea>
          <button @click="submitVote" :disabled="!voteTarget || !voteReasoning">提交投票</button>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import GameTimer from './GameTimer.vue';

const route = useRoute();
const gameId = route.params.gameId as string;
const playerId = localStorage.getItem('player_id') || '';

// State
const phase = ref<'waiting' | 'playing' | 'trial' | 'revealed' | 'finished'>('playing');
const script = ref<{ title: string }>({ title: '' });
const players = ref<Record<string, { name: string; role_id: string }>>({});
const messages = ref<Array<{ from: string; content: string }>>([]);
const currentEvent = ref('');
const newMessage = ref('');

// Accusation state
const showAccusation = ref(false);
const targetRole = ref('');
const reasoning = ref('');

// Vote state
const voteTarget = ref('');
const voteReasoning = ref('');

const messageContainer = ref<HTMLElement | null>(null);

const phaseText = computed(() => {
  const map: Record<string, string> = {
    waiting: '等待中',
    playing: '游戏中',
    trial: '审判阶段',
    revealed: '真相揭晓',
    finished: '游戏结束'
  };
  return map[phase.value] || phase.value;
});

const playerCount = computed(() => Object.keys(players.value).length);

// Fetch game state
async function fetchState() {
  try {
    const res = await fetch(`/api/rooms/${gameId}`);
    if (!res.ok) return;
    const data = await res.json();
    phase.value = data.phase || 'playing';
    players.value = data.players || {};
    
    // Build messages from public_messages if available
    if (data.public_messages && data.public_messages.length > 0) {
      messages.value = data.public_messages.map((m: any) => ({
        from: m.from_player_id,
        content: m.content
      }));
    }
    
    // Scroll to bottom
    await nextTick();
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  } catch (e) {
    console.error('Failed to fetch state:', e);
  }
}

// Send chat message
async function sendMessage() {
  const text = newMessage.value.trim();
  if (!text || !playerId) return;
  
  try {
    await fetch(`/api/rooms/${gameId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, message: text, is_private: false })
    });
    newMessage.value = '';
    await fetchState();
  } catch (e) {
    console.error('Failed to send message:', e);
  }
}

// Request clue from DM
async function requestClue() {
  try {
    await fetch(`/api/rooms/${gameId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, message: '[请求线索]', is_private: false })
    });
    await fetchState();
  } catch (e) {
    console.error('Failed to request clue:', e);
  }
}

// Start accusation
function startAccusation() {
  showAccusation.value = true;
}

// Submit accusation
async function submitAccusation() {
  if (!targetRole.value || !reasoning.value) return;
  
  try {
    await fetch(`/api/rooms/${gameId}/votes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_player_id: playerId,
        target_role_name: targetRole.value,
        reasoning: reasoning.value
      })
    });
    showAccusation.value = false;
    targetRole.value = '';
    reasoning.value = '';
    await fetchState();
  } catch (e) {
    console.error('Failed to submit accusation:', e);
  }
}

// Submit vote
async function submitVote() {
  if (!voteTarget.value || !voteReasoning.value) return;
  
  try {
    await fetch(`/api/rooms/${gameId}/votes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_player_id: playerId,
        target_role_name: voteTarget.value,
        reasoning: voteReasoning.value
      })
    });
    voteTarget.value = '';
    voteReasoning.value = '';
    await fetchState();
  } catch (e) {
    console.error('Failed to submit vote:', e);
  }
}

onMounted(() => {
  fetchState();
  // Poll every 3 seconds
  const interval = setInterval(fetchState, 3000);
  return () => clearInterval(interval);
});
</script>

<style scoped>
.game-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.game-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid #333;
}

.game-header h1 {
  font-size: 20px;
  color: #eee;
}

.phase-badge {
  padding: 4px 12px;
  background: #e94560;
  border-radius: 12px;
  font-size: 12px;
  color: #fff;
}

.game-body {
  display: flex;
  flex: 1;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.event-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  flex-shrink: 0;
}

.event-section h2 {
  font-size: 16px;
  color: #aaa;
  margin-bottom: 12px;
}

.event-content {
  background: rgba(0, 0, 0, 0.2);
  padding: 12px;
  border-radius: 6px;
  line-height: 1.6;
  color: #ddd;
}

.no-event {
  color: #666;
  font-style: italic;
}

.chat-section {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-section h2 {
  font-size: 16px;
  color: #aaa;
  margin-bottom: 12px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  min-height: 0;
}

.message-item {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.sender {
  font-weight: bold;
  color: #e94560;
  margin-right: 8px;
}

.text {
  color: #ddd;
}

.chat-input-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.chat-input-row input {
  flex: 1;
  padding: 10px;
  border: 1px solid #444;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  color: #eee;
}

.chat-input-row button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #e94560;
  color: #fff;
  cursor: pointer;
}

.side-panel {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.players-section, .actions-section, .accusation-section, .vote-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
}

h2 {
  font-size: 14px;
  color: #aaa;
  margin-bottom: 12px;
}

.player-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.role-tag {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.actions-section button {
  width: 100%;
  padding: 10px;
  margin-bottom: 8px;
  border: none;
  border-radius: 6px;
  background: #0f3460;
  color: #eee;
  cursor: pointer;
}

.actions-section button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.accusation-section select,
.vote-section select {
  width: 100%;
  padding: 8px;
  margin-bottom: 8px;
  border: 1px solid #444;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  color: #eee;
}

.accusation-section textarea,
.vote-section textarea {
  width: 100%;
  height: 80px;
  padding: 8px;
  margin-bottom: 8px;
  border: 1px solid #444;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  color: #eee;
  resize: vertical;
}

.accusation-section button,
.vote-section button {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 6px;
  background: #e94560;
  color: #fff;
  cursor: pointer;
}

.cancel-btn {
  background: #333 !important;
  margin-top: 8px;
}

.accusation-buttons {
  display: flex;
  flex-direction: column;
}
</style>
