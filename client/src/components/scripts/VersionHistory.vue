<template>
  <div class="version-history">
    <div class="version-header">
      <h2>版本历史</h2>
      <button @click="close" class="close-btn">×</button>
    </div>

    <div v-if="loading" class="loading-state">
      <p>加载中...</p>
    </div>

    <div v-else-if="versions.length === 0" class="empty-state">
      <p>暂无版本历史</p>
    </div>

    <div v-else class="versions-list">
      <div
        v-for="(version, index) in versions"
        :key="version.version_id"
        class="version-item"
        :class="{ current: index === 0 }"
      >
        <div class="version-info">
          <div class="version-badge">v{{ version.version_number }}</div>
          <div class="version-meta">
            <span class="version-date">{{ formatDate(version.created_at) }}</span>
            <span v-if="version.created_by" class="version-author">by {{ version.created_by }}</span>
          </div>
          <p v-if="version.notes" class="version-notes">{{ version.notes }}</p>
        </div>

        <div class="version-actions">
          <button @click="viewVersion(version)" class="action-btn">查看</button>
          <button 
            v-if="index > 0" 
            @click="confirmRestore(version)" 
            class="restore-btn"
          >
            恢复
          </button>
        </div>
      </div>
    </div>

    <!-- Version Detail Modal -->
    <div v-if="showDetail && selectedVersion" class="modal-overlay" @click="closeDetail">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>版本详情 - v{{ selectedVersion.version_number }}</h3>
          <button @click="closeDetail" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <pre class="version-data">{{ JSON.stringify(selectedVersion.data, null, 2) }}</pre>
        </div>
        <div class="modal-footer">
          <button @click="closeDetail" class="cancel-btn">关闭</button>
        </div>
      </div>
    </div>

    <!-- Restore Confirmation Modal -->
    <div v-if="showRestoreConfirm && versionToRestore" class="modal-overlay" @click="cancelRestore">
      <div class="modal-content confirm-modal" @click.stop>
        <div class="modal-header">
          <h3>确认恢复版本</h3>
          <button @click="cancelRestore" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p>确定要恢复到版本 v{{ versionToRestore.version_number }} 吗？</p>
          <p class="warning">这将创建一个新的版本快照，当前版本不会被删除。</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelRestore" class="cancel-btn">取消</button>
          <button @click="executeRestore" :disabled="restoring" class="restore-btn">
            {{ restoring ? '恢复中...' : '确认恢复' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const props = defineProps<{
  scriptId: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'version-restored', versionId: string): void;
}>();

const versions = ref<any[]>([]);
const loading = ref(false);
const showDetail = ref(false);
const selectedVersion = ref<any>(null);
const showRestoreConfirm = ref(false);
const versionToRestore = ref<any>(null);
const restoring = ref(false);

onMounted(() => {
  loadVersions();
});

async function loadVersions() {
  loading.value = true;
  try {
    const response = await fetch(`/api/scripts/${props.scriptId}/versions`);
    if (!response.ok) throw new Error('Failed to load versions');
    const data = await response.json();
    versions.value = data.versions || [];
  } catch (error) {
    console.error('Failed to load versions:', error);
  } finally {
    loading.value = false;
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function viewVersion(version: any) {
  // Fetch full version data
  fetch(`/api/scripts/${props.scriptId}/versions/${version.version_id}`)
    .then(res => res.json())
    .then(data => {
      selectedVersion.value = data;
      showDetail.value = true;
    })
    .catch(err => console.error('Failed to load version:', err));
}

function closeDetail() {
  showDetail.value = false;
  selectedVersion.value = null;
}

function confirmRestore(version: any) {
  versionToRestore.value = version;
  showRestoreConfirm.value = true;
}

function cancelRestore() {
  showRestoreConfirm.value = false;
  versionToRestore.value = null;
}

async function executeRestore() {
  if (!versionToRestore.value) return;
  
  restoring.value = true;
  try {
    const response = await fetch(
      `/api/scripts/${props.scriptId}/versions/${versionToRestore.value.version_id}/restore`,
      { method: 'POST' }
    );
    
    if (!response.ok) throw new Error('Failed to restore version');
    
    const data = await response.json();
    emit('version-restored', data.new_version_id);
    close();
  } catch (error) {
    console.error('Failed to restore:', error);
    alert('恢复失败，请重试');
  } finally {
    restoring.value = false;
    showRestoreConfirm.value = false;
    versionToRestore.value = null;
  }
}

function close() {
  emit('close');
}
</script>

<style scoped>
.version-history {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  max-height: 600px;
  overflow-y: auto;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.version-header h2 {
  font-size: 20px;
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 24px;
  line-height: 1;
}

.close-btn:hover {
  color: var(--text-primary);
}

.loading-state, .empty-state {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.versions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.version-item:hover {
  border-color: var(--border-medium);
}

.version-item.current {
  border-color: var(--accent-primary);
  background: var(--accent-primary-light);
}

.version-info {
  flex: 1;
}

.version-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--accent-primary);
  color: white;
  border-radius: var(--radius-round);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: var(--space-xs);
}

.version-meta {
  display: flex;
  gap: var(--space-md);
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.version-notes {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}

.version-actions {
  display: flex;
  gap: var(--space-sm);
}

.action-btn, .restore-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-medium);
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
}

.action-btn:hover {
  background: var(--bg-secondary);
  border-color: var(--accent-primary);
}

.restore-btn {
  background: var(--accent-warning-light);
  border-color: var(--accent-warning);
  color: var(--accent-warning-dark);
}

.restore-btn:hover {
  background: var(--accent-warning);
  color: white;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  max-width: 800px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.modal-header h3 {
  font-size: 18px;
  margin: 0;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  margin-bottom: var(--space-lg);
}

.version-data {
  background: var(--bg-secondary);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}

.cancel-btn {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-medium);
  background: transparent;
  color: var(--text-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background: var(--bg-secondary);
}

.confirm-modal {
  max-width: 400px;
}

.warning {
  color: var(--accent-warning-dark);
  font-size: 13px;
  margin-top: var(--space-md);
}
</style>
