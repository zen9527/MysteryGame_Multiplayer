<template>
  <div class="waiting-lobby">
    <h1>🎭 等待大厅</h1>
    <p class="room-id">房间号: {{ gameId }}</p>

    <!-- Admin section (only shown to room creator) -->
    <div v-if="isAdmin" class="admin-section">
      <h2>⚙️ 管理员设置</h2>

      <!-- LLM Test -->
      <div class="llm-test-row">
        <button @click="testLLM" :disabled="testingLLM" class="test-btn">
          {{ testingLLM ? `测试中... (${llmTestResult?.response_time_ms || 0}ms)` : '🔌 测试 LLM 连接' }}
        </button>
        <span v-if="llmTestStatus" :class="'status-' + llmTestStatus">
          {{ llmTestStatus === 'connected' ? '✅ 已连接' : '❌ 连接失败' }}
        </span>
      </div>

      <!-- Genre Selection -->
      <div class="genre-form">
        <label>剧本类型</label>
        <select v-model="selectedGenre">
          <option v-for="g in genres" :key="g.value" :value="g.value">{{ g.label }}</option>
        </select>

        <label>难度</label>
        <select v-model="selectedDifficulty">
          <option v-for="d in difficulties" :key="d">{{ d }}</option>
        </select>

        <label>预计时长（分钟）</label>
        <input type="number" v-model.number="estimatedTime" min="30" max="180" />

        <button @click="generateScript" :disabled="generating || !isAdmin" class="generate-btn">
          {{ generating ? '🤖 生成中...' : '🎲 生成剧本' }}
        </button>
      </div>

      <!-- Script Preview/Editor -->
      <ScriptEditor
        v-if="generatedScript"
        :script="generatedScript"
        @confirm="confirmScript"
        @regenerate="generateScript"
      />

      <p v-if="genError" class="error">{{ genError }}</p>
    </div>

    <!-- Player list (shown to everyone) -->
    <div class="player-list-section">
      <h2>👥 玩家列表</h2>
      <div v-if="Object.keys(players).length === 0" class="no-players">
        暂无玩家加入
      </div>
      <div v-for="(player, pid) in players" :key="pid" class="player-card">
        <span class="player-name">{{ player.name }}</span>
        <span v-if="player.role_name" class="role-badge">{{ player.role_name }}</span>
        <button v-if="isAdmin && pid !== adminId" @click="kickPlayer(pid)" class="kick-btn">踢出</button>
      </div>
      <p class="count">{{ playerCount }} 玩家</p>
    </div>

    <!-- Start button -->
    <button
      v-if="canStart"
      @click="startGame"
      :disabled="starting || !isAdmin"
      class="start-btn"
    >
      {{ starting ? '开始中...' : '🎬 开始游戏' }}
    </button>
    <p v-if="!canStart && isAdmin" class="hint">
      {{ !generatedScript ? '请先生成剧本' : '至少需要2名玩家才能开始' }}
    </p>

    <!-- Share room link -->
    <div class="share-section">
      <p>分享房间号给好友：</p>
      <input :value="gameId" readonly @click="$refs.roomInput?.select()" ref="roomInput" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import ScriptEditor from './ScriptEditor.vue';

const router = useRouter();
const route = useRoute();
const gameId = route.params.gameId as string;
const adminId = localStorage.getItem('player_id') || '';

// Admin state
const isAdmin = ref(false);
const genres = ref<Array<{ value: string; label: string }>>([]);
const difficulties = ref<string[]>(['简单', '中等', '困难']);
const selectedGenre = ref('悬疑推理');
const selectedDifficulty = ref('中等');
const estimatedTime = ref(90);

// Script generation
const generating = ref(false);
const generatedScript = ref<any | null>(null);
const genError = ref('');

// LLM test
const testingLLM = ref(false);
const llmTestStatus = ref<'connected' | 'error' | ''>('');
const llmTestResult = ref<any>(null);

// Players
const players = ref<Record<string, { name: string; role_id: string; role_name?: string }>>({});
const playerCount = computed(() => Object.keys(players.value).length);
const canStart = computed(
  () => isAdmin.value && generatedScript.value !== null && playerCount.value >= 2,
);

// Game start
const starting = ref(false);

async function loadGenres() {
  try {
    const res = await fetch('/api/genres');
    if (res.ok) {
      const data = await res.json();
      genres.value = data.genres;
      difficulties.value = data.difficulties;
    }
  } catch { /* use defaults */ }
}

async function testLLM() {
  testingLLM.value = true;
  llmTestStatus.value = '';
  try {
    const res = await fetch('/api/test-llm', { method: 'POST' });
    const data = await res.json();
    llmTestResult.value = data;
    llmTestStatus.value = data.status === 'connected' ? 'connected' : 'error';
  } catch {
    llmTestStatus.value = 'error';
  } finally {
    testingLLM.value = false;
  }
}

async function generateScript() {
  generating.value = true;
  genError.value = '';
  try {
    const res = await fetch(`/api/rooms/${gameId}/generate-script`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        genre: selectedGenre.value,
        difficulty: selectedDifficulty.value,
        estimated_time: estimatedTime.value,
        player_count: Math.max(estimatedTime.value > 60 ? 6 : 4, playerCount.value),
      }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '生成失败');
    }
    // Fetch the generated script from room state
    await fetchState();
  } catch (e: any) {
    genError.value = e.message;
  } finally {
    generating.value = false;
  }
}

async function confirmScript() {
  // Script is already saved on server via generate-script endpoint
  // This just confirms we're ready to proceed
  console.log('Script confirmed');
}

async function fetchState() {
  try {
    const res = await fetch(`/api/rooms/${gameId}`);
    if (!res.ok) return;
    const data = await res.json();
    players.value = data.players || {};
    isAdmin.value = data.room_creator_id === adminId;

    // If script is generated, show it
    if (data.script_generated && !generatedScript.value) {
      // Fetch full script details — for now we know it's generated
      generatedScript.value = {
        title: data.script?.title || '已生成',
        genre: data.script?.genre || '',
        roles_count: data.script?.roles_count || 0,
        roles: [], // Full role details would need a separate endpoint
        clues: data.clues || [],
      };
    }

    if (data.phase !== 'waiting') {
      router.push(`/game/${gameId}`);
    }
  } catch { /* ignore */ }
}

async function kickPlayer(pid: string) {
  try {
    await fetch(`/api/rooms/${gameId}/players/${pid}/kick`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: adminId }),
    });
    await fetchState();
  } catch (e) {
    console.error('Kick failed:', e);
  }
}

async function startGame() {
  if (!canStart.value || starting.value) return;
  starting.value = true;
  try {
    const res = await fetch(`/api/rooms/${gameId}/start`, { method: 'POST' });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '开始失败');
    }
    router.push(`/game/${gameId}`);
  } catch (e: any) {
    alert(e.message);
  } finally {
    starting.value = false;
  }
}

onMounted(async () => {
  await loadGenres();
  fetchState();
  const interval = setInterval(fetchState, 3000);
  return () => clearInterval(interval);
});
</script>

<style scoped>
.waiting-lobby {
  max-width: 700px;
  margin: 40px auto;
  padding: 0 16px;
}
h1 { text-align: center; color: #eee; }
.room-id { text-align: center; color: #888; margin-bottom: 24px; font-family: monospace; }

.admin-section {
  background: rgba(233, 69, 96, 0.1);
  border: 1px solid rgba(233, 69, 96, 0.3);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}
.admin-section h2 { color: #e94560; font-size: 16px; margin-bottom: 12px; }

.llm-test-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.test-btn {
  padding: 8px 16px; border: none; border-radius: 6px;
  background: #333; color: #eee; cursor: pointer; font-size: 13px;
}
.status-connected { color: #27ae60; }
.status-error { color: #e94560; }

.genre-form { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.genre-form label { font-size: 13px; color: #aaa; }
.genre-form select, .genre-form input {
  padding: 8px; border: 1px solid #444; border-radius: 6px;
  background: rgba(0, 0, 0, 0.3); color: #eee;
}
.generate-btn {
  padding: 12px; border: none; border-radius: 6px;
  background: linear-gradient(135deg, #e94560, #0f3460);
  color: #fff; font-size: 15px; cursor: pointer; margin-top: 8px;
}
.generate-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.player-list-section { margin-bottom: 24px; }
.player-list-section h2 { color: #aaa; font-size: 16px; margin-bottom: 12px; }
.no-players { color: #666; text-align: center; padding: 24px; }

.player-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: rgba(255, 255, 255, 0.05);
  border-radius: 6px; margin-bottom: 8px;
}
.player-name { font-size: 15px; }
.role-badge { font-size: 12px; color: #e94560; }
.kick-btn {
  padding: 4px 10px; border: none; border-radius: 4px;
  background: #c0392b; color: #fff; cursor: pointer; font-size: 12px;
}

.count { color: #888; text-align: center; margin-bottom: 16px; }

.start-btn {
  display: block; width: 100%; padding: 14px; border: none; border-radius: 8px;
  background: linear-gradient(135deg, #27ae60, #2ecc71);
  color: #fff; font-size: 18px; cursor: pointer;
}
.start-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.hint { text-align: center; color: #e94560; margin-top: 8px; }

.share-section {
  margin-top: 24px; text-align: center; padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.share-section p { color: #888; font-size: 13px; margin-bottom: 8px; }
.share-section input {
  width: 100%; max-width: 400px; padding: 8px; text-align: center;
  border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3);
  color: #aaa; font-family: monospace; cursor: pointer;
}

.error { color: #e94560; margin-top: 8px; }
</style>
