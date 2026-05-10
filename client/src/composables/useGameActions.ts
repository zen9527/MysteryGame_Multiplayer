import { useGameStore } from '../stores/game';
import { storeToRefs } from 'pinia';

/**
 * Game actions composable - provides game state and actions
 */
export function useGameActions() {
  const store = useGameStore();
  const { phase, act, currentEvent, players, clues, publicMessages, privateMessages } = storeToRefs(store);

  // Admin actions
  const startGame = async () => {
    await store.startGame();
  };

  const advanceAct = async () => {
    await store.advanceAct();
  };

  const forceTrial = async () => {
    await store.forceTrial();
  };

  const endGame = async () => {
    await store.endGame();
  };

  // Player actions
  const sendChat = async (content: string) => {
    await store.sendPublicChat(content);
  };

  const submitAccusation = async (targetId: string, reasoning: string) => {
    await store.submitAccusation(targetId, reasoning);
  };

  const castVote = async (targetId: string) => {
    await store.castVote(targetId);
  };

  const requestAdvance = async () => {
    await store.requestAdvance();
  };

  return {
    // State
    phase,
    act,
    currentEvent,
    players,
    clues,
    publicMessages,
    privateMessages,
    
    // Admin actions
    startGame,
    advanceAct,
    forceTrial,
    endGame,
    
    // Player actions
    sendChat,
    submitAccusation,
    castVote,
    requestAdvance
  };
}
