<template>
  <div class="admin-panel">
    <h3>🛠️ 管理员控制台</h3>

    <div class="admin-actions">
      <button @click="$emit('push-event')" :disabled="loading" class="action-btn advance">
        ⏭️ {{ loading ? '生成中...' : '推进剧情' }}
      </button>
      <button @click="showClueInput = true" class="action-btn clue">🔍 追加线索</button>
      <button @click="$emit('force-trial')" class="action-btn trial">⚖️ 强制审判</button>
      <button @click="$emit('end-game')" class="action-btn end">🛑 提前结束</button>
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
      <summary>📋 DM日志 ({{ dmLog.length }}条)</summary>
      <div class="dm-log">
        <div v-for="(log, i) in dmLog" :key="i" class="log-entry">{{ log }}</div>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  loading: boolean;
  dmLog: string[];
}>();

const emit = defineEmits(['push-event', 'force-trial', 'end-game', 'add-clue']);

const showClueInput = ref(false);
const clueTitle = ref('');
const clueContent = ref('');

function submitClue() {
  if (!clueTitle.value || !clueContent.value) return;
  emit('add-clue', { title: clueTitle.value, content: clueContent.value });
  showClueInput.value = false;
  clueTitle.value = '';
  clueContent.value = '';
}
</script>

<style scoped>
.admin-panel {
  background: rgba(233, 69, 96, 0.1);
  border: 1px solid rgba(233, 69, 96, 0.3);
  border-radius: 8px;
  padding: 12px;
}
.admin-panel h3 { color: #e94560; font-size: 14px; margin-bottom: 10px; }

.admin-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.action-btn {
  padding: 8px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; color: #fff;
}
.action-btn.advance { background: #0f3460; }
.action-btn.clue { background: #2980b9; }
.action-btn.trial { background: #d35400; }
.action-btn.end { background: #c0392b; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.clue-modal {
  margin-top: 12px; padding: 12px; background: rgba(0, 0, 0, 0.3); border-radius: 6px;
}
.clue-modal h4 { color: #eee; font-size: 14px; margin-bottom: 8px; }
.clue-modal input, .clue-modal textarea {
  width: 100%; padding: 8px; margin-bottom: 8px; border: 1px solid #444;
  border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; resize: vertical;
}
.modal-actions { display: flex; gap: 8px; }
.confirm-btn { padding: 8px 16px; border: none; border-radius: 6px; background: #27ae60; color: #fff; cursor: pointer; }
.cancel-btn { padding: 8px 16px; border: none; border-radius: 6px; background: #333; color: #eee; cursor: pointer; }

.dm-log { max-height: 200px; overflow-y: auto; margin-top: 8px; }
.log-entry { padding: 4px 0; font-size: 12px; color: #888; border-bottom: 1px solid rgba(255,255,255,0.05); }

details summary { cursor: pointer; color: #e94560; font-size: 13px; margin-top: 8px; }
</style>
