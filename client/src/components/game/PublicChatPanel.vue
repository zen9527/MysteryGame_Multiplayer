<script setup lang="ts">
import { useGameActions } from '../../composables/useGameActions';
import { ref } from 'vue';

const { publicMessages, sendChat } = useGameActions();
const newMessage = ref('');

const sendPublicChat = async () => {
  if (!newMessage.value.trim()) return;
  await sendChat(newMessage.value);
  newMessage.value = '';
};
</script>

<template>
  <div class="public-chat-panel">
    <h2>💬 公共聊天</h2>
    <div class="messages">
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
</template>

<style scoped>
.public-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

h2 {
  margin-bottom: 12px;
  color: #333;
}

.messages {
  flex: 1;
  overflow-y: auto;
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
}

.message-item {
  margin-bottom: 10px;
  padding: 8px;
  border-radius: 4px;
}

.message-item.dm-message {
  background: #e3f2fd;
  border-left: 3px solid #2196f3;
}

.sender {
  font-weight: bold;
  color: #555;
  margin-right: 8px;
}

.text {
  color: #333;
}

.chat-input-row {
  display: flex;
  gap: 8px;
}

input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  padding: 8px 16px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #45a049;
}
</style>
