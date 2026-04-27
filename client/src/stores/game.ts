import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { WSMessage } from '../types/ws';

export interface RoleCardData {
  name?: string;
  description?: string;
  background?: string;
  secret_task?: string;
  alibi?: string;
  relationships?: Array<{ target: string; description: string }>;
  motive?: string;
}

export interface ClueData {
  id: string;
  title: string;
  content: string;
  content_hint: string;
  is_red_herring: boolean;
}

export const useGameStore = defineStore('game', () => {
  const phase = ref<'waiting' | 'playing' | 'trial' | 'revealed' | 'finished'>('waiting');
  const act = ref(1);
  const messages = ref<WSMessage[]>([]);
  const players = ref<Map<string, { name: string; role_id: string }>>(new Map());
  const currentEvent = ref<string>('');

  // New state for private information
  const roleCard = ref<{ layer1: RoleCardData | null; layer2: RoleCardData | null; layer3: RoleCardData | null }>({
    layer1: null,
    layer2: null,
    layer3: null,
  });
  const privateMessages = ref<Array<{ from: string; content: string; timestamp: string }>>([]);
  const clues = ref<Map<string, ClueData>>(new Map());
  const activeTab = ref<'role' | 'private' | 'clue' | 'action'>('role');

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
        // Legacy — handled by role_card messages now
        break;
      case 'chat':
        // Public chat — already in messages
        break;
      case 'private_chat':
        // Player private chat — add to privateMessages
        privateMessages.value.push({
          from: msg.from === 'playerId' ? '我' : msg.from,
          content: msg.content,
          timestamp: msg.timestamp || '',
        });
        break;
      case 'role_card':
        // Layered role card
        const layer = msg.layer as '1' | '2' | '3';
        if (layer === '1') roleCard.value.layer1 = msg.data as RoleCardData;
        else if (layer === '2') roleCard.value.layer2 = msg.data as RoleCardData;
        else if (layer === '3') roleCard.value.layer3 = msg.data as RoleCardData;
        break;
      case 'dm_private':
        // DM → player private message
        if (msg.to === 'playerId') {
          privateMessages.value.push({
            from: '🎭 DM',
            content: msg.content,
            timestamp: '',
          });
        }
        break;
      case 'clue_unlock':
        // Clue unlocked for this player
        const clue = msg.clue as ClueData;
        clues.value.set(clue.id, clue);
        break;
      case 'trial_start':
        phase.value = 'trial';
        act.value = 3;
        break;
      case 'vote_result':
        // Vote results — public
        break;
      case 'reveal':
        phase.value = 'revealed';
        break;
      case 'game_over':
        phase.value = 'finished';
        break;
      case 'phase_unlock':
        phase.value = msg.phase as typeof phase.value;
        act.value = msg.act;
        break;
      case 'player_left':
        players.value.delete(msg.player_name);
        break;
    }
  }

  return {
    phase,
    act,
    messages,
    players,
    currentEvent,
    roleCard,
    privateMessages,
    clues,
    activeTab,
    handleWSMessage,
  };
});
