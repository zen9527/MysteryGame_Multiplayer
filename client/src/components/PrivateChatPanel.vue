<template>
  <div class="private-chat">
    <div v-if="!hasPlayer" class="no-player">
      <p>等待加入游戏...</p>
    </div>
    <div v-else class="chat-content">
      <div class="messages" ref="messageContainer">
        <div
          v-for="(msg, i) in privateMessages"
          :key="i"
          class="message-item"
          :class="{ 'dm-message': msg.from === '🎭 DM' }"
        >
          <span class="sender">{{ msg.from }}</span>
          <span class="text">{{ msg.content }}</span>
        </div>
      </div>
      <div v-if="isStreaming" class="streaming-status">
        🤖 DM正在思考...
      </div>
      <div v-if="pendingReply" class="pending-reply">
        <span class="sender">🎭 DM</span>
        <span class="text">{{ pendingReply }}</span>
      </div>
      <div class="chat-input-row">
        <input
          v-model="newMessage"
          @keyup.enter="sendDMPrivate"
          placeholder="向DM提问..."
        />
        <button @click="sendDMPrivate" :disabled="!newMessage.trim() || isStreaming">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useGameStore } from '../stores/game';
import { useRoute } from 'vue-router';

const store = useGameStore();
const route = useRoute();
const gameId = route.params.gameId as string;
const playerId =
  localStorage.getItem(`player_${gameId}`) ||
  localStorage.getItem(`admin_${gameId}`) ||
  '';

const newMessage = ref('');
const messageContainer = ref<HTMLElement | null>(null);

const privateMessages = computed(() => store.privateMessages);
const hasPlayer = computed(() => !!playerId);

// Streaming state
const isStreaming = ref(false);
const pendingReply = ref('');

async function sendDMPrivate() {
  const text = newMessage.value.trim();
  if (!text || !playerId || isStreaming.value) return;

  isStreaming.value = true;
  pendingReply.value = '';
  newMessage.value = '';

  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/chat-response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_id: playerId,
        content: text,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error('DM回复失败:', err.detail || '未知错误');
      pendingReply.value = 'DM 暂时无法回应，请稍后再试。';
      return;
    }

    // Consume SSE stream — same pattern as GamePage.vue handlePushEvent
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
                console.log('[chat-response] DM starting...');
                break;
              case 'chunk':
                pendingReply.value += data.content;
                await nextTick();
                if (messageContainer.value) {
                  messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
                }
                break;
              case 'done':
                store.privateMessages.push({
                  from: '🎭 DM',
                  content: data.content,
                  timestamp: '',
                });
                console.log(`[chat-response] Done: ${data.content.length} chars`);
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
  } catch (e: any) {
    console.warn('DM私信请求失败:', e);
    pendingReply.value = 'DM 暂时无法回应，请稍后再试。';
  } finally {
    isStreaming.value = false;
  }

  await nextTick();
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
}

onMounted(() => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  });
});
</script>

<style scoped>
.private-chat {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.no-player {
  text-align: center;
  color: #666;
  padding: 24px;
}
.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
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
.dm-message {
  background: rgba(233, 69, 96, 0.1);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 4px;
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
.chat-input-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.streaming-status {
  text-align: center; color: #e94560; font-size: 13px; margin-bottom: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

.pending-reply {
  padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.pending-reply .sender { font-weight: bold; color: #e94560; margin-right: 8px; }
.pending-reply .text { color: #ddd; font-size: 13px; line-height: 1.6; }
</style>
