<!-- client/src/components/game/ChatArea.vue -->
<template>
  <div class="chat-container">
    <div class="chat-area" ref="chatContainer">
      <div 
        v-for="msg in messages" 
        :key="msg.id"
        class="message"
        :class="{ dm: msg.from === 'DM' }"
      >
        <div class="message-header">
          <span class="message-from">{{ msg.from }}</span>
          <span class="message-time">{{ msg.timestamp }}</span>
        </div>
        <div class="message-content">{{ msg.content }}</div>
      </div>
    </div>
    
    <div class="chat-input-area">
      <textarea
        v-model="inputText"
        class="chat-input"
        rows="3"
        :placeholder="mode === 'public' ? '输入你的推理或问题...' : '向 DM 提问...'"
        @keyup.enter="handleEnter"
      ></textarea>
      <div class="chat-actions">
        <div class="chat-mode-toggle">
          <button 
            class="mode-btn" 
            :class="{ active: mode === 'public' }"
            @click="$emit('update:mode', 'public')"
          >
            📢 公开讨论
          </button>
          <button 
            class="mode-btn" 
            :class="{ active: mode === 'private' }"
            @click="$emit('update:mode', 'private')"
          >
            💬 DM 私聊
          </button>
        </div>
        <button class="send-btn" @click="handleSend">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

interface ChatMessage {
  id: string;
  from: string;
  content: string;
  timestamp: string;
}

const props = withDefaults(defineProps<{
  messages: ChatMessage[];
  mode?: 'public' | 'private';
}>(), {
  mode: 'public'
});

const emit = defineEmits<{
  'update:mode': [mode: 'public' | 'private'];
  send: [message: string, mode: 'public' | 'private'];
}>();

const inputText = ref('');
const chatContainer = ref<HTMLElement | null>(null);

function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) return;
  e.preventDefault();
  handleSend();
}

function handleSend() {
  if (!inputText.value.trim()) return;
  emit('send', inputText.value.trim(), props.mode || 'public');
  inputText.value = '';
}

watch(() => props.messages, () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
}, { deep: true });
</script>

<style scoped>
@import '../../styles/variables.css';

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xl);
}

.message {
  margin-bottom: var(--space-lg);
}

.message.dm {
  background: rgba(210, 168, 255, 0.08);
  border-left: 3px solid var(--accent-secondary);
  padding: var(--space-md);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.message.player {
  background: rgba(255, 255, 255, 0.03);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.message-from {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-primary);
}

.message.dm .message-from {
  color: var(--accent-secondary);
}

.message-time {
  font-size: 10px;
  color: var(--text-muted);
}

.message-content {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

.chat-input-area {
  padding: var(--space-lg) var(--space-xl);
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid var(--border-light);
  flex-shrink: 0;
}

.chat-input {
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 13px;
  resize: none;
  transition: all var(--transition-fast);
}

.chat-input:focus {
  outline: none;
  border-color: var(--focus-border);
  background: rgba(255, 255, 255, 0.06);
}

.chat-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-sm);
}

.chat-mode-toggle {
  display: flex;
  gap: var(--space-xs);
}

.mode-btn {
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-btn.active {
  background: rgba(121, 192, 255, 0.15);
  border-color: var(--border-accent);
  color: var(--accent-primary);
}

.send-btn {
  padding: 8px 20px;
  background: var(--accent-primary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--bg-primary);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.send-btn:hover {
  background: #5fa8e8;
}
</style>
