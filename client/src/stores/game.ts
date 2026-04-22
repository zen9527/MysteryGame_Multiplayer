import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { WSMessage } from '../types/ws';

export const useGameStore = defineStore('game', () => {
  const phase = ref<'waiting' | 'playing' | 'trial' | 'revealed' | 'finished'>('waiting');
  const messages = ref<WSMessage[]>([]);
  const players = ref<Map<string, { name: string; role_id: string }>>(new Map());
  const currentEvent = ref<string>('');

  function handleWSMessage(msg: WSMessage) {
    messages.value.push(msg);

    switch (msg.type) {
      case 'system':
      case 'event':
        currentEvent.value = msg.content;
        break;
      case 'player_joined':
        players.value.set(msg.player_name, { name: msg.player_name, role_id: '' });
        break;
      case 'role_assigned':
        // 更新玩家角色
        break;
      case 'chat':
        // 添加到聊天消息
        break;
      case 'trial_start':
        phase.value = 'trial';
        break;
      case 'reveal':
        phase.value = 'revealed';
        break;
      case 'game_over':
        phase.value = 'finished';
        break;
    }
  }

  return {
    phase,
    messages,
    players,
    currentEvent,
    handleWSMessage
  };
});
