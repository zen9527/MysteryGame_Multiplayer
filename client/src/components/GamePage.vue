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
            <AdminPanel
              v-if="isAdmin && activeTab === 'action'"
              :loading="adminLoading"
              :dm-log="dmLog"
              @push-event="handlePushEvent"
              @advance-act="handleAdvanceAct"
              @force-trial="handleForceTrial"
              @end-game="handleEndGame"
              @add-clue="handleAddClue"
            />
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
} from '../constants';
import { WebSocketManager } from '../utils/ws';
import type { ClientMessage } from '../types/ws';
import GameTimer from './GameTimer.vue';
import AdminPanel from './AdminPanel.vue';
import RoleCard from './RoleCard.vue';
import PrivateChatPanel from './PrivateChatPanel.vue';
import ClueCardPanel from './ClueCardPanel.vue';

const route = useRoute();
const gameId = route.params.gameId as string;
const playerId = localStorage.getItem(`player_${gameId}`) || localStorage.getItem(`admin_${gameId}`) || localStorage.getItem('player_id') || '';

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
let wsManager: WebSocketManager | null = null;
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

// WebSocket connection using WebSocketManager with exponential backoff
function connectWebSocket() {
  wsManager = new WebSocketManager(gameId, playerId);

  wsManager.connect(
    (msg) => {
      // Route through store for state management
      store.handleWSMessage(msg as any);

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
    },
    () => {}
  );
}

function sendWSMessage(type: "join" | "chat" | "private_chat" | "role_read" | "accuse" | "vote" | "request_advance", data: Record<string, any> = {}) {
  wsManager?.send({ type, ...data } as ClientMessage);
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
    setTimeout(() => { requestingClue.value = false; }, REQUEST_CLUE_TIMEOUT);
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
  const interval = setInterval(fetchState, FETCH_STATE_INTERVAL);
  return () => clearInterval(interval);
});

onUnmounted(() => {
  wsManager?.disconnect();
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
.event-content.generating { background: rgba(233, 69, 96, 0.15); color: #e94560; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.no-event { color: #666; font-style: italic; }

.act-banner { background: linear-gradient(135deg, #8e44ad, #0f3460); border-radius: 8px; padding: 16px; margin-bottom: 16px; animation: banner-appear 0.5s ease-out; }
.act-banner-content { text-align: center; }
.act-banner-title { font-size: 18px; font-weight: bold; color: #fff; display: block; margin-bottom: 8px; }
.act-banner-text { font-size: 13px; color: #ddd; line-height: 1.6; }
@keyframes banner-appear { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

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

.side-panel { width: 360px; flex-shrink: 0; display: flex; flex-direction: column; overflow-y: auto; max-height: calc(100vh - 80px); }

.tab-nav { display: flex; gap: 4px; margin-bottom: 8px; }
.tab-nav button {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  color: #aaa;
  cursor: pointer;
  font-size: 13px;
}
.tab-nav button.active {
  background: #e94560;
  color: #fff;
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.players-section, .actions-section, .accusation-section, .vote-section, .reveal-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
h2 { font-size: 14px; color: #aaa; margin-bottom: 12px; }

.player-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.role-tag { font-size: 12px; color: #e94560; }
.admin-tag { font-size: 12px; color: #f39c12; font-weight: bold; }

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
