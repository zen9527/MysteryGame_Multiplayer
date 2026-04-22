<template>
  <div class="chat-panel">
    <div class="messages">
      <div v-for="msg in messages" :key="msg.id">
        <strong>{{ msg.from }}</strong>: {{ msg.content }}
      </div>
    </div>
    <input v-model="newMessage" @keyup.enter="send" placeholder="输入消息..." />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const messages = ref<any[]>([]);
const newMessage = ref('');

function send() {
  if (newMessage.value.trim()) {
    // 发送消息
    newMessage.value = '';
  }
}
</script>
