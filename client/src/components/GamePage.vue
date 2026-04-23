<template>
  <div class="game-page">
    <!-- Header -->
    <header class="game-header">
      <h1>{{ scriptTitle || '剧本杀' }}</h1>
      <span class="phase-badge">{{ phaseText }} (第{{ act }}幕)</span>
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
          <div v-else class="no-event">等待DM发布事件...</div>
        </div>

        <!-- Chat Panel -->
        <div class="chat-section">
          <h2>💬 聊天</h2>
          <div class="messages" ref="messageContainer">
            <div v-for="(msg, i) in messages" :key="i" class="message-item" :class="{ 'dm-message': msg.from === '__dm__' }">
              <span class="sender">{{ msg.from === '__dm__' ? '🎭 DM' : msg.from }}</span>
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
        <!-- Admin Panel (only for admin) -->
        <AdminPanel
          v-if="isAdmin"
          :loading="adminLoading"
          :dm-log="dmLog"
          @push-event="handlePushEvent"
          @force-trial="handleForceTrial"
          @end-game="handleEndGame"
          @add-clue="handleAddClue"
        />

        <!-- Player List -->
        <div class="players-section">
          <h2>👥 玩家 ({{ playerCount }})</h2>
          <div v-for="(player, pid) in players" :key="pid" class="player-item">
            <span>{{ player.name }}</span>
            <span class="role-tag">{{ player.role_name || '#' + player.role_id.slice(-4) }}</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div v-if="phase === 'playing'" class="actions-section">
          <h2>⚡ 操作</h2>
          <button @click="requestClue" :disabled="phase !== 'playing'">请求线索</button>
          <button @click="startAccusation" :disabled="phase !== 'playing'">开始指控</button>
        </div>

        <!-- Accusation Panel -->
        <div v-if="showAccusation" class="accusation-section">
          <h2>🔍 指控凶手</h2>
          <select v-model="targetRole">
            <option value="">选择目标...</option>
            <option v-for="(player, pid) in players" :key="pid" :value="player.role_id || player.name">
              {{ player.name }} ({{ player.role_name || '角色' }})
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
            <option v-for="(player, pid) in players" :key="pid" :value="player.role_id || player.name">
              {{ player.name }} ({{ player.role_name || '角色' }})
            </option>
          </select>
          <textarea v-model="voteReasoning" placeholder="写下你的推理..."></textarea>
          <button @click="submitVote" :disabled="!voteTarget || !voteReasoning">提交投票</button>
        </div>

        <!-- Reveal Section -->
        <div v-if="phase === 'revealed'" class="reveal-section">
          <h2>📢 真相揭晓</h2>
          <p>{{ currentEvent || '游戏已结束' }}</p>
          <button @click="$router.push('/')" class="back-btn">返回首页</button>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import GameTimer from './GameTimer.vue';
import AdminPanel from './AdminPanel.vue';

const route = useRoute();
const gameId = route.params.gameId as string;
const playerId = localStorage.getItem('player_id') || '';

// State
const phase = ref<'waiting' | 'playing' | 'trial' | 'revealed' | 'finished'>('playing');
const act = ref(1);
const scriptTitle = ref('');
const players = ref<Record<string, { name: string; role_id: string; role_name?: string }>>({});
const messages = ref<Array<{ from: string; content: string }>>([]);
const currentEvent = ref('');
const newMessage = ref('');
const isAdmin = ref(false);
const dmLog = ref<string[]>([]);

// Accusation state
const showAccusation = ref(false);
const targetRole = ref('');
const reasoning = ref('');

// Vote state
const voteTarget = ref('');
const voteReasoning = ref('');

// Admin loading state
const adminLoading = ref(false);

// WebSocket
let ws: WebSocket | null = null;
const messageContainer = ref<HTMLElement | null>(null);

const phaseText = computed(() => {
  const map: Record<string, string> = {
    waiting: '等待中', playing: '游戏中', trial: '审判阶段', revealed: '真相揭晓', finished: '游戏结束'
  };
  return map[phase.value] || phase.value;
});

const playerCount = computed(() => Object.keys(players.value).length);

// Fetch game state via HTTP
async function fetchState() {
  try {
    const res = await fetch(`/api/rooms/${gameId}`);
    if (!res.ok) return;
    const data = await res.json();
    phase.value = data.phase || 'playing';
    act.value = data.act || 1;
    players.value = data.players || {};
    isAdmin.value = data.room_creator_id === playerId;

    // Update messages from server
    if (data.public_messages && data.public_messages.length > 0) {
      const existingCount = messages.value.length;
      const newMessages = data.public_messages.slice(existingCount);
      for (const m of newMessages) {
        messages.value.push({ from: m.from_player_id, content: m.content });
        if (m.type === 'event') {
          currentEvent.value = m.content;
        }
      }
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

// WebSocket connection
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/${gameId}/${playerId}`);

  ws.onopen = () => console.log('WS connected');

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    switch (msg.type) {
      case 'chat':
        messages.value.push({ from: msg.from, content: msg.content });
        break;
      case 'event':
        currentEvent.value = msg.content;
        messages.value.push({ from: '__dm__', content: msg.content });
        break;
      case 'system':
        messages.value.push({ from: '系统', content: msg.content });
        break;
      case 'accusation':
        messages.value.push({ from: msg.from, content: `指控 ${msg.target}: ${msg.reasoning}` });
        break;
      case 'trial_start':
        phase.value = 'trial';
        act.value = 3;
        break;
      case 'reveal':
        phase.value = 'revealed';
        currentEvent.value = JSON.stringify(msg.truth);
        break;
      case 'game_over':
        phase.value = 'finished';
        break;
    }
    nextTick(() => {
      if (messageContainer.value) messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    });
  };

  ws.onclose = () => {
    console.log('WS disconnected, reconnecting...');
    setTimeout(connectWebSocket, 3000);
  };
}

function sendWSMessage(type: string, data: Record<string, any> = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, ...data }));
  }
}

// Send chat message
async function sendMessage() {
  const text = newMessage.value.trim();
  if (!text || !playerId) return;

  // Send via WebSocket (real-time) and HTTP (persistence)
  sendWSMessage('chat', { content: text });

  try {
    await fetch(`/api/rooms/${gameId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, message: text, is_private: false }),
    });
  } catch (e) { console.error(e); }

  newMessage.value = '';
}

async function requestClue() {
  sendWSMessage('chat', { content: '[请求线索]' });
  try {
    await fetch(`/api/rooms/${gameId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, message: '[请求线索]', is_private: false }),
    });
  } catch (e) { console.error(e); }
}

function startAccusation() { showAccusation.value = true; }

async function submitAccusation() {
  if (!targetRole.value || !reasoning.value) return;
  sendWSMessage('accuse', { target_role_name: targetRole.value, reasoning: reasoning.value });
  try {
    await fetch(`/api/rooms/${gameId}/votes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_player_id: playerId, target_role_name: targetRole.value, reasoning: reasoning.value }),
    });
  } catch (e) { console.error(e); }
  showAccusation.value = false;
  targetRole.value = '';
  reasoning.value = '';
}

async function submitVote() {
  if (!voteTarget.value || !voteReasoning.value) return;
  try {
    await fetch(`/api/rooms/${gameId}/votes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_player_id: playerId, target_role_name: voteTarget.value, reasoning: voteReasoning.value }),
    });
  } catch (e) { console.error(e); }
  voteTarget.value = '';
  voteReasoning.value = '';
}

// Admin actions
async function handlePushEvent() {
  adminLoading.value = true;
  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/push-event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, event_content: '' }),
    });
    if (res.ok) {
      const data = await res.json();
      currentEvent.value = data.content;
    } else {
      alert('推进剧情失败');
    }
  } catch (e) { console.error(e); } finally { adminLoading.value = false; }
}

async function handleAddClue(clue: { title: string; content: string }) {
  try {
    await fetch(`/api/rooms/${gameId}/dm/add-clue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, clue_title: clue.title, clue_content: clue.content }),
    });
  } catch (e) { console.error(e); }
}

async function handleForceTrial() {
  if (!confirm('确定要强制进入审判阶段吗？')) return;
  try {
    await fetch(`/api/rooms/${gameId}/force-trial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId }),
    });
    phase.value = 'trial';
    act.value = 3;
  } catch (e) { console.error(e); }
}

async function handleEndGame() {
  if (!confirm('确定要提前结束游戏并揭晓真相吗？')) return;
  try {
    await fetch(`/api/rooms/${gameId}/end-game`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId }),
    });
    phase.value = 'revealed';
  } catch (e) { console.error(e); }
}

onMounted(() => {
  fetchState();
  connectWebSocket();
  const interval = setInterval(fetchState, 5000); // Slower polling since we have WS
  return () => clearInterval(interval);
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<style scoped>
.game-page { min-height: 100vh; display: flex; flex-direction: column; }
.game-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; background: rgba(0, 0, 0, 0.3); border-bottom: 1px solid #333; }
.game-header h1 { font-size: 20px; color: #eee; }
.phase-badge { padding: 4px 12px; background: #e94560; border-radius: 12px; font-size: 12px; color: #fff; }
.game-body { display: flex; flex: 1; gap: 16px; padding: 16px; overflow: hidden; }
.main-panel { flex: 1; display: flex; flex-direction: column; gap: 16px; min-width: 0; }

.event-section { background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 16px; flex-shrink: 0; max-height: 200px; overflow-y: auto; }
.event-section h2 { font-size: 16px; color: #aaa; margin-bottom: 12px; }
.event-content { background: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 6px; line-height: 1.6; color: #ddd; white-space: pre-wrap; }
.no-event { color: #666; font-style: italic; }

.chat-section { flex: 1; background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; min-height: 0; }
.chat-section h2 { font-size: 16px; color: #aaa; margin-bottom: 12px; }
.messages { flex: 1; overflow-y: auto; padding-right: 8px; min-height: 0; }
.message-item { padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.dm-message { background: rgba(233, 69, 96, 0.1); padding: 8px; border-radius: 4px; margin-bottom: 4px; }
.sender { font-weight: bold; color: #e94560; margin-right: 8px; }
.text { color: #ddd; }

.chat-input-row { display: flex; gap: 8px; margin-top: 12px; }
.chat-input-row input { flex: 1; padding: 10px; border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; }
.chat-input-row button { padding: 10px 20px; border: none; border-radius: 6px; background: #e94560; color: #fff; cursor: pointer; }

.side-panel { width: 320px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; max-height: calc(100vh - 80px); }
.players-section, .actions-section, .accusation-section, .vote-section, .reveal-section { background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 16px; }
h2 { font-size: 14px; color: #aaa; margin-bottom: 12px; }

.player-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.role-tag { font-size: 12px; color: #666; }

.actions-section button { width: 100%; padding: 10px; margin-bottom: 8px; border: none; border-radius: 6px; background: #0f3460; color: #eee; cursor: pointer; }
.actions-section button:disabled { opacity: 0.5; cursor: not-allowed; }

.accusation-section select, .vote-section select { width: 100%; padding: 8px; margin-bottom: 8px; border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; }
.accusation-section textarea, .vote-section textarea { width: 100%; height: 80px; padding: 8px; margin-bottom: 8px; border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; resize: vertical; }
.accusation-section button, .vote-section button { width: 100%; padding: 10px; border: none; border-radius: 6px; background: #e94560; color: #fff; cursor: pointer; }
.cancel-btn { background: #333 !important; margin-top: 8px; }
.accusation-buttons { display: flex; flex-direction: column; }

.reveal-section p { line-height: 1.8; color: #ddd; white-space: pre-wrap; }
.back-btn { padding: 10px 24px; border: none; border-radius: 6px; background: #0f3460; color: #eee; cursor: pointer; margin-top: 12px; }
</style>
