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

const VALID_PHASES = ['waiting', 'playing', 'trial', 'revealed', 'finished'] as const;
type ValidPhase = (typeof VALID_PHASES)[number];

export const useGameStore = defineStore('game', () => {
  const phase = ref<ValidPhase>('waiting');
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
  const clues = ref<Array<ClueData>>([]);
  const activeTab = ref<'role' | 'private' | 'clue' | 'action'>('role');

  function handleWSMessage(msg: WSMessage) {
    messages.value.push(msg);

    switch (msg.type) {
      case 'system':
      case 'event':
        currentEvent.value = msg.content;
        break;
      case 'player_joined':
        // Add to players map if not already present
        if (!Array.from(players.value.values()).some(p => p.name === msg.player_name)) {
          players.value.set(msg.player_name, { name: msg.player_name, role_id: '' });
        }
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
          from: msg.from,
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
        privateMessages.value.push({
          from: '🎭 DM',
          content: msg.content,
          timestamp: '',
        });
        break;
      case 'clue_unlock':
        // Clue unlocked for this player
        const clue = msg.clue as ClueData;
        clues.value.push(clue);
        break;
      case 'clue_reveal':
        // Clue reveal — add to public messages if public, private if not
        if (msg.public) {
          currentEvent.value = `🔍 新线索（公开）：${(msg.clue as any).title} — ${(msg.clue as any).content}`;
        }
        break;
      case 'accusation':
        // Accusation — already in messages
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
        if (VALID_PHASES.includes(msg.phase as ValidPhase)) {
          phase.value = msg.phase as ValidPhase;
          act.value = msg.act;
        }
        break;
      case 'player_left':
        for (const [pid, p] of players.value) {
          if (p.name === msg.player_name) {
            players.value.delete(pid);
            break;
          }
        }
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
