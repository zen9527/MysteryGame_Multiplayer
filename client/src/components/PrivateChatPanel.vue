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
      <div class="chat-input-row">
        <input
          v-model="newMessage"
          @keyup.enter="sendDMPrivate"
          placeholder="回复DM..."
        />
        <button @click="sendDMPrivate" :disabled="!newMessage.trim()">发送</button>
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

async function sendDMPrivate() {
  const text = newMessage.value.trim();
  if (!text || !playerId) return;

  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/private`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_id: playerId,
        to_player_id: playerId,
        content: text,
      }),
    });
    if (res.ok) {
      newMessage.value = '';
    }
  } catch (e) {
    console.error('DM private failed:', e);
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
</style>
