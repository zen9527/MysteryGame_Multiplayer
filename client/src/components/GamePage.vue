<template>
  <div class="game-page">
    <!-- Header -->
    <header class="game-header">
      <h1>{{ scriptTitle || '剧本杀' }}</h1>
      <span class="phase-badge">{{ phaseText }} (第{{ act }}幕)</span>
      <GameTimer :total-seconds="timerSeconds" />
    </header>

    <!-- Main content -->
    <div class="game-body">
      <!-- Left: Public info -->
      <div class="main-panel">
        <!-- DM Event Display -->
        <div class="event-section">
          <h2>📜 公共事件</h2>
          <div v-if="adminLoading" class="event-content generating">
            🤖 DM正在生成事件...
          </div>
          <div v-else-if="currentEvent" class="event-content">{{ currentEvent }}</div>
          <div v-else class="no-event">等待DM发布事件...</div>
        </div>

        <!-- Act Transition Banner -->
        <div v-if="actBanner" class="act-banner">
          <div class="act-banner-content">
            <span class="act-banner-title">📖 第{{ actBanner.act }}幕开始</span>
            <span v-if="actBanner.plot_summary" class="act-banner-text">{{ actBanner.plot_summary }}</span>
          </div>
        </div>

        <!-- Public Chat -->
        <div class="chat-section">
          <h2>💬 公共聊天</h2>
          <div class="messages" ref="messageContainer">
            <div
              v-for="(msg, i) in publicMessages"
              :key="i"
              class="message-item"
              :class="{ 'dm-message': msg.from === '🎭 DM' || msg.isEvent }"
            >
              <span class="sender">{{ msg.from }}</span>
              <span class="text">{{ msg.content }}</span>
            </div>
          </div>
          <div class="chat-input-row">
            <input v-model="newMessage" @keyup.enter="sendPublicChat" placeholder="输入公共消息..." />
            <button @click="sendPublicChat">发送</button>
          </div>
        </div>
      </div>

      <!-- Right: Private info tabs -->
      <aside class="side-panel">
        <!-- Tab Navigation -->
        <div class="tab-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.icon }} {{ tab.label }}
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- Role Card Tab -->
          <RoleCard v-if="activeTab === 'role'" />

          <!-- Private Chat Tab -->
          <PrivateChatPanel v-if="activeTab === 'private'" />

          <!-- Clues Tab -->
          <ClueCardPanel v-if="activeTab === 'clue'" />

          <!-- Actions Tab -->
          <div v-if="activeTab === 'action'" class="actions-panel">
            <!-- Player List (name + role) -->
            <div class="players-section">
              <h2>👥 玩家 ({{ playerCount }})</h2>
              <div v-for="player in playersList" :key="player.pid" class="player-item">
                <span>{{ player.name }}</span>
                <span v-if="player.role_id && roleLookup[player.role_id]" class="role-tag">{{ roleLookup[player.role_id] }}</span>
                <span v-else-if="player.role_id" class="role-tag">待分配</span>
                <span v-if="player.pid === roomCreatorId" class="admin-tag">👑</span>
              </div>
            </div>

            <!-- Action Buttons -->
            <div v-if="phase === 'playing'" class="actions-section">
              <h2>⚡ 操作</h2>
              <button @click="requestClue" :disabled="phase !== 'playing' || requestingClue">
                {{ requestingClue ? '⏳ 请求中...' : '请求线索' }}
              </button>
              <button @click="showAccusation = true" :disabled="phase !== 'playing'">开始指控</button>
            </div>

            <!-- Accusation Panel -->
            <div v-if="showAccusation && phase === 'playing'" class="accusation-section">
              <h2>🔍 指控凶手</h2>
              <select v-model="targetRole">
                <option value="">选择目标...</option>
                <option v-for="(player, pid) in playersList" :key="pid" :value="player.role_id || player.name">
                  {{ player.name }}
                </option>
              </select>
              <textarea v-model="reasoning" placeholder="写下你的推理..."></textarea>
              <div class="accusation-buttons">
                <button @click="submitAccusation" :disabled="!targetRole || !reasoning || submittingAccusation">{{ submittingAccusation ? '提交中...' : '提交指控' }}</button>
                <button @click="showAccusation = false" class="cancel-btn">取消</button>
              </div>
            </div>

            <!-- Vote Panel -->
            <div v-if="phase === 'trial'" class="vote-section">
              <h2>🗳️ 投票环节</h2>
              <select v-model="voteTarget">
                <option value="">选择目标...</option>
                <option v-for="(player, pid) in playersList" :key="pid" :value="player.role_id || player.name">
                  {{ player.name }}
                </option>
              </select>
              <textarea v-model="voteReasoning" placeholder="写下你的推理..."></textarea>
              <button @click="submitVote" :disabled="!voteTarget || !voteReasoning || submittingVote">{{ submittingVote ? '提交中...' : '提交投票' }}</button>
            </div>

            <!-- Reveal Section -->
            <div v-if="phase === 'revealed'" class="reveal-section">
              <h2>📢 真相揭晓</h2>
              <p>{{ currentEvent || '游戏已结束' }}</p>
              <button @click="$router.push('/')" class="back-btn">返回首页</button>
            </div>

            <!-- Admin Panel -->
            <div v-if="isAdmin && activeTab === 'action'" class="admin-panel">
              <h3>🛠️ 管理员控制台</h3>

              <div class="admin-actions">
                <button @click="handlePushEvent" :disabled="adminLoading" class="action-btn advance">
                  ⏭️ {{ adminLoading ? '生成中...' : '推进剧情' }}
                </button>
                <button @click="handleAdvanceAct" :disabled="adminLoading" class="action-btn next-act">
                  📖 {{ adminLoading ? '处理中...' : '推进下一幕' }}
                </button>
                <button @click="showClueInput = true" :disabled="adminLoading" class="action-btn clue">🔍 追加线索</button>
                <button @click="handleForceTrial" :disabled="adminLoading" class="action-btn trial">⚖️ 强制审判</button>
                <button @click="handleEndGame" :disabled="adminLoading" class="action-btn end">🛑 提前结束</button>
              </div>

              <!-- Clue input modal -->
              <div v-if="showClueInput" class="clue-modal">
                <h4>追加线索</h4>
                <input v-model="clueTitle" placeholder="线索标题" />
                <textarea v-model="clueContent" placeholder="线索内容..." rows="3"></textarea>
                <div class="modal-actions">
                  <button @click="submitClue" :disabled="!clueTitle || !clueContent" class="confirm-btn">发布</button>
                  <button @click="showClueInput = false" class="cancel-btn">取消</button>
                </div>
              </div>

              <!-- DM Log toggle -->
              <details v-if="dmLog.length > 0">
                <summary>📋 DM 日志 ({{ dmLog.length }}条)</summary>
                <div class="dm-log">
                  <div v-for="(log, i) in dmLog" :key="i" class="log-entry">{{ log }}</div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { useGameStore } from '../stores/game';
import { storeToRefs } from 'pinia';
import {
  REQUEST_CLUE_TIMEOUT,
  FETCH_STATE_INTERVAL,
  WS_MAX_RECONNECT_ATTEMPTS,
  WS_BASE_RECONNECT_DELAY,
} from '../constants';
import type { WSMessage, ClientMessage } from '../types/ws';
import GameTimer from './GameTimer.vue';
import RoleCard from './RoleCard.vue';
import PrivateChatPanel from './PrivateChatPanel.vue';
import ClueCardPanel from './ClueCardPanel.vue';

const route = useRoute();
const gameId = route.params.gameId as string;
const playerId = localStorage.getItem(`player_${gameId}`) || localStorage.getItem(`admin_${gameId}`) || localStorage.getItem('player_id') || '';

// Admin panel state
const showClueInput = ref(false);
const clueTitle = ref('');
const clueContent = ref('');

function submitClue() {
  if (!clueTitle.value || !clueContent.value) return;
  handleAddClue({ title: clueTitle.value, content: clueContent.value });
  showClueInput.value = false;
  clueTitle.value = '';
  clueContent.value = '';
}

const store = useGameStore();
const { phase, act, currentEvent, activeTab, players: storePlayers, publicMessages, actBanner } = storeToRefs(store);

// State local to this component
const scriptTitle = ref('');
const newMessage = ref('');
const isAdmin = ref(false);
const roomCreatorId = ref('');
const dmLog = ref<string[]>([]);
const timerSeconds = ref(3600);
const roleLookup = ref<Record<string, string>>({});

// Tabs
const tabs = [
  { key: 'role' as const, icon: '📋', label: '角色卡' },
  { key: 'private' as const, icon: '💌', label: '私信' },
  { key: 'clue' as const, icon: '🔍', label: '线索' },
  { key: 'action' as const, icon: '⚡', label: '操作' },
];

// Accusation state
const showAccusation = ref(false);
const targetRole = ref('');
const reasoning = ref('');

// Vote state
const voteTarget = ref('');
const voteReasoning = ref('');

// Admin loading state
const adminLoadingBase = ref(false);

// Player action loading state
const requestingClue = ref(false);
const submittingAccusation = ref(false);
const submittingVote = ref(false);
const addingClue = ref(false);
const advancingAct = ref(false);
const forcingTrial = ref(false);

// Combined admin loading — any admin action disables all admin buttons
const adminLoading = computed(() =>
  adminLoadingBase.value || advancingAct.value || addingClue.value || forcingTrial.value
);

// WebSocket
let ws: WebSocket | null = null;
let reconnectAttempts = 0;
let fetchInterval: ReturnType<typeof setInterval> | null = null;
let clueTimeout: ReturnType<typeof setTimeout> | null = null;
const messageContainer = ref<HTMLElement | null>(null);

// Convert players Map to array with keys for v-for
const playersList = computed<Array<{ pid: string; name: string; role_id: string }>>(() => {
  return Array.from(storePlayers.value.entries()).map(([pid, p]) => ({ pid: pid as string, ...p }));
});

const phaseText = computed(() => {
  const map: Record<string, string> = {
    waiting: '等待中', playing: '游戏中', trial: '审判阶段', revealed: '真相揭晓', finished: '游戏结束'
  };
  return map[phase.value] || phase.value;
});

const playerCount = computed(() => playersList.value.length);

// Fetch game state via HTTP
async function fetchState() {
  try {
    const res = await fetch(`/api/rooms/${gameId}`);
    if (!res.ok) return;
    const data = await res.json();
    phase.value = data.phase || 'playing';
    act.value = data.act || 1;
    roomCreatorId.value = data.room_creator_id || '';
    isAdmin.value = data.room_creator_id === playerId;

    if (phase.value === 'playing') {
      timerSeconds.value = 90 * 60;
    }

    // Build role lookup table (role_id → role_name)
    if (data.script?.roles) {
      roleLookup.value = {};
      for (const role of data.script.roles) {
        roleLookup.value[role.id] = role.name;
      }
    }

    // Update players in store
    for (const [pid, p] of Object.entries(data.players || {})) {
      storePlayers.value.set(pid, { name: (p as any).name, role_id: (p as any).role_id });
    }

    // Load public messages from API into store (deduplicated)
    if (data.public_messages && data.public_messages.length > 0) {
      store.loadPublicMessagesFromAPI(data.public_messages);
    }

    await nextTick();
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  } catch (e) {
    console.error('Failed to fetch state:', e);
  }
}

// WebSocket connection with native API and exponential backoff
function connectWebSocket() {
  // Close existing connection before creating a new one
  if (ws) {
    ws.onclose = null;
    ws.close();
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${protocol}//${window.location.host}/ws/${gameId}/${playerId}`;
  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WSMessage;
      // Route through store for state management
      store.handleWSMessage(msg);

      // Clear requestingClue when an event comes back from DM
      if (msg.type === 'event') {
        requestingClue.value = false;
      }

      // Scroll to bottom for any chat/event messages
      if (msg.type === 'chat' || msg.type === 'event') {
        nextTick(() => {
          if (messageContainer.value) messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
        });
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = (event) => {
    // Handle different close codes
    const CLOSE_CODE_ROOM_NOT_FOUND = 4001;
    const CLOSE_CODE_PLAYER_NOT_FOUND = 4002;
    const CLOSE_CODE_GAME_FINISHED = 4003;

    if (event.code === CLOSE_CODE_ROOM_NOT_FOUND || 
        event.code === CLOSE_CODE_PLAYER_NOT_FOUND ||
        event.code === CLOSE_CODE_GAME_FINISHED) {
      // Invalid connection - don't reconnect
      return;
    }

    // Attempt reconnection with exponential backoff
    if (reconnectAttempts < WS_MAX_RECONNECT_ATTEMPTS) {
      const delay = WS_BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts);
      setTimeout(() => connectWebSocket(), delay);
      reconnectAttempts++;
    }
  };
}

function sendWSMessage(type: "join" | "chat" | "private_chat" | "role_read" | "accuse" | "vote" | "request_advance", data: Record<string, any> = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, ...data } as ClientMessage));
  }
}

// Send public chat (WS only — server handles persistence)
async function sendPublicChat() {
  const text = newMessage.value.trim();
  if (!text || !playerId) return;

  sendWSMessage('chat', { content: text });
  newMessage.value = '';
}

async function requestClue() {
  if (requestingClue.value) return;
  requestingClue.value = true;
  sendWSMessage('request_advance');
  // The server will generate an event and broadcast it via WS.
  // Auto-reset loading after 15 seconds (LLM may take a while but will broadcast when done).
  if (clueTimeout) clearTimeout(clueTimeout);
  clueTimeout = setTimeout(() => { requestingClue.value = false; }, REQUEST_CLUE_TIMEOUT);
}

  async function submitAccusation() {
    if (!targetRole.value || !reasoning.value || submittingAccusation.value) return;
    submittingAccusation.value = true;
    sendWSMessage('accuse', { target_role_name: targetRole.value, reasoning: reasoning.value });
    try {
      const res = await fetch(`/api/rooms/${gameId}/accusations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_player_id: playerId, target_role_name: targetRole.value, reasoning: reasoning.value }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '提交指控失败');
      }
    } catch (e) {
      alert('提交指控失败: 网络错误');
    } finally {
      submittingAccusation.value = false;
    }
    showAccusation.value = false;
    targetRole.value = '';
    reasoning.value = '';
  }

  async function submitVote() {
    if (!voteTarget.value || !voteReasoning.value || submittingVote.value) return;
    submittingVote.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/votes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_player_id: playerId, target_role_name: voteTarget.value, reasoning: voteReasoning.value }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '提交投票失败');
      }
    } catch (e) {
      alert('提交投票失败: 网络错误');
    } finally {
      submittingVote.value = false;
    }
    voteTarget.value = '';
    voteReasoning.value = '';
  }

// Admin actions
async function handlePushEvent() {
  adminLoadingBase.value = true;
  currentEvent.value = '';
  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/push-event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error('推进剧情失败:', err.detail || '未知错误');
      return;
    }

    // Consume SSE stream — same pattern as WaitingLobby.vue generateScript
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            let data;
            try {
              data = JSON.parse(line.slice(6));
            } catch {
              /* skip malformed SSE */
              continue;
            }
            switch (data.type) {
              case 'start':
                break;
              case 'chunk':
                // Token streaming — no UI feedback needed (adminLoading stays true)
                break;
              case 'done':
                currentEvent.value = data.public_event || '';
                break;
              case 'error':
                throw new Error(data.message);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (e) {
    console.warn('推进剧情请求失败:', e);
  } finally {
    adminLoadingBase.value = false;
  }
}

  async function handleAddClue(clue: { title: string; content: string }) {
    addingClue.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/dm/add-clue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId, clue_title: clue.title, clue_content: clue.content }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '追加线索失败');
      }
    } catch (e) {
      alert('追加线索失败: 网络错误');
    } finally {
      addingClue.value = false;
    }
  }

  async function handleAdvanceAct() {
    if (!confirm(`确定要推进到第${act.value + 1}幕吗？这将解锁新的角色卡、线索和私信。`)) return;
    advancingAct.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/advance-act`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '推进失败');
      } else {
        fetchState();
      }
    } catch (e) {
      alert('推进失败: 网络错误');
    } finally {
      advancingAct.value = false;
    }
  }

  async function handleForceTrial() {
    if (!confirm('确定要强制进入审判阶段吗？')) return;
    forcingTrial.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/force-trial`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '操作失败');
      } else {
        fetchState();
      }
    } catch (e) {
      alert('操作失败: 网络错误');
    } finally {
      forcingTrial.value = false;
    }
  }

  async function handleEndGame() {
    if (!confirm('确定要提前结束游戏并揭晓真相吗？')) return;
    adminLoadingBase.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/end-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '结束游戏失败');
        return;
      }

      // Consume SSE stream
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                switch (data.type) {
                  case 'start':
                    currentEvent.value = '🎭 正在揭晓真相...';
                    break;
                  case 'done':
                    currentEvent.value = data.content || '';
                    fetchState();
                    break;
                  case 'error':
                    console.error('[end-game] Error:', data.message);
                    break;
                }
              } catch { /* skip malformed SSE */ }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (e) {
      console.error('结束游戏失败:', e);
      alert('结束游戏失败: 网络错误');
    } finally {
      adminLoadingBase.value = false;
    }
  }

onMounted(() => {
  fetchState();
  connectWebSocket();
  fetchInterval = setInterval(fetchState, FETCH_STATE_INTERVAL);
});

onUnmounted(() => {
  if (fetchInterval) clearInterval(fetchInterval);
  if (clueTimeout) clearTimeout(clueTimeout);
  if (ws) {
    ws.onclose = null;
    ws.close();
  }
});
</script>

<style scoped>
@import '../styles/variables.css';

.game-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px); /* Account for sidebar */
  padding: var(--space-lg);
  background: var(--bg-primary);
}

.game-header {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-lg);
}

.game-header h1 {
  font-size: 24px;
  color: var(--text-primary);
}

.phase-badge {
  padding: var(--space-xs) var(--space-md);
  background: var(--accent-primary);
  color: var(--bg-primary);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
}

.game-body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-lg);
  flex: 1;
  min-height: 0;
}

.main-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  overflow-y: auto;
}

.event-section, .chat-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.event-section h2, .chat-section h2 {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.event-content {
  padding: var(--space-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  line-height: 1.6;
}

.event-content.generating {
  color: var(--accent-primary);
}

.no-event {
  color: var(--text-muted);
  padding: var(--space-md);
  text-align: center;
}

.act-banner {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  color: var(--bg-primary);
}

.act-banner-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.act-banner-title {
  font-size: 18px;
  font-weight: 700;
}

.act-banner-text {
  font-size: 14px;
  opacity: 0.9;
}

.messages {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.message-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.message-item.dm-message {
  background: rgba(121, 192, 255, 0.1);
  border-left: 3px solid var(--accent-primary);
}

.sender {
  font-weight: bold;
  color: var(--accent-secondary);
  margin-right: var(--space-sm);
}

.text {
  color: var(--text-primary);
}

.chat-input-row {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.chat-input-row input {
  flex: 1;
  padding: var(--space-md);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.chat-input-row button {
  padding: var(--space-md) var(--space-xl);
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent-primary);
  color: var(--bg-primary);
  cursor: pointer;
  font-weight: 600;
}

.chat-input-row button:hover {
  opacity: 0.9;
}

.side-panel {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  max-height: calc(100vh - 80px);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.tab-nav {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}

.tab-nav button {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all var(--transition-fast);
}

.tab-nav button.active {
  background: var(--accent-primary);
  color: var(--bg-primary);
  font-weight: 600;
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.players-section, .actions-section, .accusation-section, .vote-section, .reveal-section {
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-md);
}

.players-section h2, .actions-section h2 {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.player-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--border-light);
}

.role-tag {
  font-size: 12px;
  color: var(--accent-secondary);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(210, 168, 255, 0.1);
  border-radius: var(--radius-sm);
}

.admin-tag {
  font-size: 12px;
  color: #f39c12;
  font-weight: bold;
}

.actions-section button {
  width: 100%;
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.actions-section button:hover:not(:disabled) {
  background: var(--accent-primary);
  color: var(--bg-primary);
}

.actions-section button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.accusation-section select, .vote-section select {
  width: 100%;
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.accusation-section textarea, .vote-section textarea {
  width: 100%;
  height: 80px;
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  resize: vertical;
}

.accusation-section button, .vote-section button {
  width: 100%;
  padding: var(--space-md);
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent-primary);
  color: var(--bg-primary);
  cursor: pointer;
  font-weight: 600;
}

.cancel-btn {
  background: var(--bg-primary) !important;
  margin-top: var(--space-sm);
}

.accusation-buttons {
  display: flex;
  flex-direction: column;
}

.reveal-section p {
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
}

.back-btn {
  padding: var(--space-md) var(--space-xl);
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  cursor: pointer;
  margin-top: var(--space-md);
}

.back-btn:hover {
  background: var(--accent-primary);
  color: var(--bg-primary);
}
</style>
