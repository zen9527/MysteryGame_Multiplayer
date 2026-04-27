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

export interface ChatMessage {
  from: string;
  content: string;
  timestamp: string;
  isEvent?: boolean;
}

const VALID_PHASES = ['waiting', 'playing', 'trial', 'revealed', 'finished'] as const;
type ValidPhase = (typeof VALID_PHASES)[number];

export const useGameStore = defineStore('game', () => {
  const phase = ref<ValidPhase>('waiting');
  const act = ref(1);
  const messages = ref<WSMessage[]>([]);
  const players = ref<Map<string, { name: string; role_id: string }>>(new Map());
  const currentEvent = ref<string>('');

  // Public chat messages (fed by WS chat messages)
  const publicMessages = ref<ChatMessage[]>([]);

  // New state for private information
  const roleCard = ref<{ layer1: RoleCardData | null; layer2: RoleCardData | null; layer3: RoleCardData | null }>({
    layer1: null,
    layer2: null,
    layer3: null,
  });
  const privateMessages = ref<Array<{ from: string; content: string; timestamp: string }>>([]);
  const clues = ref<Array<ClueData>>([]);
  const activeTab = ref<'role' | 'private' | 'clue' | 'action'>('role');

  // Track which messages we've already seen (by content+from+timestamp) to prevent duplicates
  const seenMessageKeys = ref<Set<string>>(new Set());

  function _addPublicMessage(from: string, content: string, timestamp: string, isEvent = false) {
    // Key without timestamp — WS messages have timestamp="" while API messages have real timestamps
    // Same message from same sender must deduplicate regardless of source
    const key = `${from}:${content}`;
    if (seenMessageKeys.value.has(key)) return;
    seenMessageKeys.value.add(key);
    publicMessages.value.push({ from, content, timestamp, isEvent });
  }

  function handleWSMessage(msg: WSMessage) {
    messages.value.push(msg);

    switch (msg.type) {
      case 'system':
        break;
      case 'event':
        currentEvent.value = msg.content;
        _addPublicMessage('🎭 DM', msg.content, '', true);
        break;
      case 'player_joined':
        if (!Array.from(players.value.values()).some(p => p.name === msg.player_name)) {
          players.value.set(msg.player_name, { name: msg.player_name, role_id: '' });
        }
        break;
      case 'role_assigned':
        break;
      case 'chat':
        // Public chat — add to publicMessages (deduplicated)
        _addPublicMessage(msg.from, msg.content, msg.timestamp || '');
        break;
      case 'private_chat':
        privateMessages.value.push({
          from: msg.from,
          content: msg.content,
          timestamp: msg.timestamp || '',
        });
        break;
      case 'role_card': {
        const layer = msg.layer as '1' | '2' | '3';
        if (layer === '1') roleCard.value.layer1 = msg.data as RoleCardData;
        else if (layer === '2') roleCard.value.layer2 = msg.data as RoleCardData;
        else if (layer === '3') roleCard.value.layer3 = msg.data as RoleCardData;
        break;
      }
      case 'dm_private':
        privateMessages.value.push({
          from: '🎭 DM',
          content: msg.content,
          timestamp: '',
        });
        break;
      case 'clue_unlock': {
        const clue = msg.clue as ClueData;
        // Avoid duplicate clues
        if (!clues.value.some(c => c.id === clue.id)) {
          clues.value.push(clue);
        }
        break;
      }
      case 'clue_reveal':
        if (msg.public) {
          currentEvent.value = `🔍 新线索（公开）：${(msg.clue as any).title} — ${(msg.clue as any).content}`;
        }
        break;
      case 'accusation':
        break;
      case 'trial_start':
        phase.value = 'trial';
        act.value = 3;
        break;
      case 'vote_result':
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

  /** Load public messages from HTTP API response (used on initial fetchState) */
  function loadPublicMessagesFromAPI(apiMessages: Array<{ from_player_name: string; content: string; type: string; timestamp: string }>) {
    for (const m of apiMessages) {
      const from = m.type === 'event' ? '🎭 DM' : m.from_player_name;
      _addPublicMessage(from, m.content, m.timestamp || '', m.type === 'event');
    }
  }

  return {
    phase,
    act,
    messages,
    players,
    currentEvent,
    publicMessages,
    roleCard,
    privateMessages,
    clues,
    activeTab,
    handleWSMessage,
    loadPublicMessagesFromAPI,
  };
});
