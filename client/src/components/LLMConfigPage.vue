<template>
  <div class="llm-config-page">
    <header class="page-header">
      <h1>🔌 LLM 配置</h1>
      <p class="subtitle">配置 LLM 服务以支持剧本生成和游戏主持</p>
    </header>

    <section class="config-section">
      <div class="config-card">
        <!-- Endpoint -->
        <div class="config-field">
          <label for="endpoint">API 端点</label>
          <input
            id="endpoint"
            v-model="endpoint"
            placeholder="localhost:12340"
            type="text"
          />
          <p v-if="endpoint && !endpoint.startsWith('http')" class="hint">
            将自动补全为：{{ normalizeEndpoint(endpoint) }}
          </p>
        </div>

        <!-- Model -->
        <div class="config-field">
          <label for="model">模型名称</label>
          <div class="model-row">
            <select id="model" v-model="model" :disabled="!models.length">
              <option value="">-- 选择模型 --</option>
              <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
            </select>
            <button
              @click="fetchModels"
              :disabled="fetchingModels || !endpoint"
              type="button"
            >
              {{ fetchingModels ? '加载中...' : '🔍 获取模型' }}
            </button>
          </div>
          <input
            v-model="modelManual"
            placeholder="或手动输入模型名称"
            class="manual-input"
            type="text"
          />
        </div>

        <!-- API Key -->
        <div class="config-field">
          <label for="api-key">API Key</label>
          <div class="key-row">
            <input
              id="api-key"
              v-model="apiKey"
              :type="showKey ? 'text' : 'password'"
              placeholder="sk-..."
            />
            <button @click="showKey = !showKey" type="button">
              {{ showKey ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>

        <!-- Actions -->
        <div class="actions">
          <button @click="saveConfig" :disabled="saving" type="button">
            {{ saving ? '保存中...' : '💾 保存配置' }}
          </button>
          <button @click="testConnection" :disabled="testing || !endpoint" type="button">
            {{ testing ? '测试中...' : '🔌 测试连接' }}
          </button>
        </div>

        <!-- Status -->
        <div v-if="testStatus" :class="'status status-' + testStatus" role="status">
          {{ testStatus === 'connected' ? '✅ 已连接' : '❌ 连接失败' }}
        </div>
        <div v-if="testError" class="error" role="alert">{{ testError }}</div>
        <div v-if="saved" class="success" role="status">配置已保存</div>
      </div>
    </section>

    <router-link to="/" class="back-btn">← 返回房间列表</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { normalizeEndpoint } from '@/utils/endpoint';

const endpoint = ref('');
const model = ref('');
const modelManual = ref('');
const apiKey = ref('');
const models = ref<string[]>([]);
const fetchingModels = ref(false);
const saving = ref(false);
const testing = ref(false);
const showKey = ref(false);
const testStatus = ref<'connected' | 'failed' | null>(null);
const testError = ref('');
const saved = ref(false);

function effectiveModel(): string {
  return modelManual.value.trim() || model.value;
}

async function loadConfig() {
  try {
    const res = await fetch('/api/llm-config');
    if (res.ok) {
      const data = await res.json();
      endpoint.value = data.endpoint || '';
      model.value = data.model || '';
      apiKey.value = data.api_key || '';
    }
  } catch (err) {
    console.error('Failed to load config:', err);
  }
}

async function fetchModels() {
  if (!endpoint.value) return;
  fetchingModels.value = true;
  models.value = [];
  try {
    // Use backend proxy to avoid CORS issues
    const res = await fetch('/api/llm/models');
    if (res.ok) {
      const data = await res.json();
      models.value = data.data?.map((m: any) => m.id) || [];
    } else {
      console.error('Failed to fetch models:', res.status, await res.text());
      models.value = [];
    }
  } catch (err) {
    console.error('Failed to fetch models:', err);
    models.value = [];
  } finally {
    fetchingModels.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  saved.value = false;
  try {
    // First, try to get existing providers
    const listRes = await fetch('/api/llm/providers');
    let providerExists = false;
    if (listRes.ok) {
      const listData = await listRes.json();
      providerExists = listData.providers.some((p: any) => p.name === 'default');
    }

    if (providerExists) {
      // Update existing provider by deleting and recreating
      await fetch('/api/llm/providers/default', { method: 'DELETE' });
    }

    // Create/update provider
    await fetch('/api/llm/providers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'default',
        type: 'openai', // Default to OpenAI-compatible format
        endpoint: normalizeEndpoint(endpoint.value),
        model: effectiveModel(),
        api_key: apiKey.value,
      }),
    });

    // Set as active
    await fetch('/api/llm/providers/active', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'default' }),
    });

    saved.value = true;
    setTimeout(() => { saved.value = false; }, 3000);
  } catch (err) {
    console.error('Failed to save:', err);
    alert('保存失败');
  } finally {
    saving.value = false;
  }
}

async function testConnection() {
  if (!endpoint.value) return;
  testing.value = true;
  testStatus.value = null;
  testError.value = '';
  try {
    const res = await fetch('/api/llm/providers/default/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}), // Empty body but needs Content-Type header
    });
    const data = await res.json();
    if (res.ok && data.status === 'connected') {
      testStatus.value = 'connected';
    } else {
      testStatus.value = 'failed';
      testError.value = data.detail || await res.text() || '连接失败';
    }
  } catch (err) {
    testStatus.value = 'failed';
    testError.value = err instanceof Error ? err.message : '网络错误';
  } finally {
    testing.value = false;
  }
}

onMounted(() => loadConfig());
</script>

<style scoped>
.llm-config-page {
  padding: var(--space-xl);
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--space-2xl);
}

.page-header h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.config-section {
  margin-bottom: var(--space-xl);
}

.config-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
  margin-bottom: var(--space-xl);
}

.config-field {
  margin-bottom: var(--space-lg);
}

.config-field label {
  display: block;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: var(--space-sm);
  font-size: 14px;
}

.config-field input,
.config-field select {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-family);
}

.config-field input:focus,
.config-field select:focus {
  outline: none;
  border-color: var(--focus-border);
}

.config-field input::placeholder {
  color: var(--text-muted);
}

.model-row {
  display: flex;
  gap: var(--space-md);
}

.model-row select {
  flex: 1;
}

.model-row button {
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.model-row button:hover:not(:disabled) {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.model-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.manual-input {
  margin-top: var(--space-sm);
}

.key-row {
  display: flex;
  gap: var(--space-md);
}

.key-row input {
  flex: 1;
}

.key-row button {
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.key-row button:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.hint {
  margin-top: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: rgba(241, 196, 15, 0.1);
  border: 1px solid rgba(241, 196, 15, 0.3);
  border-radius: var(--radius-md);
  color: #f1c40f;
  font-size: 12px;
}

.actions {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-xl);
}

.actions button {
  padding: var(--space-lg) var(--space-xl);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.actions button:first-child {
  background: var(--accent-primary);
  color: var(--bg-primary);
}

.actions button:first-child:hover:not(:disabled) {
  opacity: 0.9;
}

.actions button:last-child {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-medium);
}

.actions button:last-child:hover:not(:disabled) {
  background: var(--hover-bg);
}

.actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status {
  margin-top: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  font-size: 14px;
}

.status-connected {
  background: rgba(46, 213, 115, 0.2);
  color: #2ed573;
  border: 1px solid rgba(46, 213, 115, 0.3);
}

.status-failed {
  background: rgba(233, 69, 96, 0.2);
  color: #e94560;
  border: 1px solid rgba(233, 69, 96, 0.3);
}

.error {
  color: #e94560;
  margin-top: var(--space-sm);
  font-size: 14px;
}

.success {
  color: #2ed573;
  margin-top: var(--space-sm);
  font-size: 14px;
}

.back-btn {
  display: inline-block;
  padding: var(--space-md) var(--space-lg);
  color: var(--accent-primary);
  text-decoration: none;
  font-size: 14px;
}

.back-btn:hover {
  text-decoration: underline;
}
</style>
