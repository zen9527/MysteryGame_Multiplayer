<template>
  <div class="room-create">
    <h1>创建游戏房间</h1>

    <section class="script-selection">
      <h2>选择剧本（可选）</h2>
      <p v-if="!selectedScript && !showScriptList && !showScriptDetail">点击"浏览剧本"选择预设剧本，或直接开始新游戏</p>
      
      <div v-if="selectedScript" class="selected-script">
        <div>
          <strong>{{ selectedScript.title }}</strong>
          <div class="script-meta">
            <span v-if="selectedScript.genre">{{ selectedScript.genre }}</span>
            <span v-if="selectedScript.difficulty">{{ selectedScript.difficulty }}</span>
            <span v-if="selectedScript.player_count">{{ selectedScript.player_count }}人</span>
          </div>
        </div>
        <button @click="clearSelection" class="change-btn">更换</button>
      </div>

      <div class="script-buttons">
        <button @click="showScriptList = true" class="browse-btn" v-if="!showScriptList && !showScriptDetail">
          浏览剧本
        </button>
        <button @click="showScriptList = false; showScriptDetail = false" class="back-btn" v-if="showScriptList || showScriptDetail">
          ← 返回
        </button>
      </div>

      <!-- Script List View -->
      <ScriptList 
        v-if="showScriptList" 
        @select="selectScriptForRoom"
      />

      <!-- Script Detail View -->
      <ScriptDetail 
        v-if="showScriptDetail && viewingScriptId" 
        :scriptId="viewingScriptId"
        @back="showScriptDetail = false"
        @start="confirmAndCreateRoom"
      />
    </section>

    <section class="player-info">
      <h2>玩家信息</h2>
      <input 
        v-model="playerName" 
        placeholder="你的名字"
        class="player-input"
        maxlength="50"
      />
    </section>

    <button @click="confirmAndCreateRoom" :disabled="!playerName" class="create-btn">
      创建房间
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '@/stores/game';
import ScriptList from '@/components/ScriptList.vue';
import ScriptDetail from '@/components/ScriptDetail.vue';

const router = useRouter();
const store = useGameStore();

const playerName = ref('');
const selectedScriptId = ref<string | null>(null);
const viewingScriptId = ref<string | null>(null);
const showScriptList = ref(false);
const showScriptDetail = ref(false);

const selectedScript = computed(() => 
  store.availableScripts.find(s => s.id === selectedScriptId.value)
);

function selectScriptForRoom(scriptId: string) {
  viewingScriptId.value = scriptId;
  selectedScriptId.value = scriptId;
  showScriptList.value = false;
  showScriptDetail.value = true;
}

function confirmAndCreateRoom() {
  if (!playerName.value) return;
  
  if (selectedScriptId.value) {
    store.selectScript(selectedScriptId.value);
  }
  createRoom();
}

async function createRoom() {
  try {
    const game_id = await store.createRoomWithScript(playerName.value, playerName.value);
    router.push(`/game/${game_id}`);
  } catch (error) {
    console.error('Failed to create room:', error);
    alert('创建房间失败，请重试');
  }
}

function clearSelection() {
  selectedScriptId.value = null;
  viewingScriptId.value = null;
  showScriptList.value = false;
  showScriptDetail.value = false;
}
</script>

<style scoped>
.room-create { padding: 20px; max-width: 800px; margin: 0 auto; }
h1 { text-align: center; margin-bottom: 30px; color: #333; }
section { margin: 30px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }
h2 { color: #333; margin-bottom: 15px; }
p { color: #666; line-height: 1.6; }
.selected-script { display: flex; justify-content: space-between; align-items: center; 
                   padding: 15px; background: #fff; border-radius: 8px; margin-bottom: 15px; }
.script-meta { display: flex; gap: 10px; margin-top: 8px; color: #666; font-size: 14px; }
.script-buttons { display: flex; gap: 10px; margin-top: 15px; }
.browse-btn, .back-btn, .change-btn { padding: 10px 20px; border: none; border-radius: 6px; 
                                       cursor: pointer; font-size: 14px; }
.browse-btn { background: #2196f3; color: white; }
.back-btn { background: #9e9e9e; color: white; }
.change-btn { background: #ff9800; color: white; }
.player-info input { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; 
                     border-radius: 8px; box-sizing: border-box; }
.create-btn { background: #4caf50; color: white; border: none; padding: 15px 30px; 
              border-radius: 8px; font-size: 18px; cursor: pointer; width: 100%; margin-top: 20px; }
.create-btn:disabled { background: #ccc; cursor: not-allowed; }
.create-btn:hover:not(:disabled) { background: #45a049; }
</style>
