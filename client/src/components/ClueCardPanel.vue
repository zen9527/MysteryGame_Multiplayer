<template>
  <div class="clue-panel">
    <div v-if="!hasClues" class="no-clues">
      <p>暂无线索</p>
    </div>
    <div v-else class="clue-list">
      <div
        v-for="clue in clueArray"
        :key="clue.id"
        class="clue-card"
        :class="{ 'new-clue': clue.new }"
      >
        <div class="clue-header" @click="toggleClue(clue.id)">
          <span class="clue-title">{{ clue.title }}</span>
          <span v-if="clue.is_red_herring" class="red-herring">⚠️ 假线索</span>
          <span class="expand-icon">{{ expandedClues[clue.id] ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedClues[clue.id]" class="clue-body">
          <p class="clue-hint">{{ clue.content_hint }}</p>
          <p class="clue-content">{{ clue.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useGameStore } from '../stores/game';

const store = useGameStore();

const clues = computed(() => store.clues);
const hasClues = computed(() => clues.value.length > 0);

const clueArray = computed(() => {
  return Array.from(clues.value).map(c => ({ ...c, new: false }));
});

const expandedClues = ref<Record<string, boolean>>({});

function toggleClue(clueId: string) {
  expandedClues.value[clueId] = !expandedClues.value[clueId];
}
</script>

<style scoped>
.clue-panel {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
}
.no-clues {
  text-align: center;
  color: #666;
  padding: 24px;
}
.clue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.clue-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  overflow: hidden;
  transition: background 0.3s;
}
.clue-card.new-clue {
  background: rgba(233, 69, 96, 0.15);
  animation: pulse 1s ease-in-out 3;
}
@keyframes pulse {
  0%, 100% { background: rgba(233, 69, 96, 0.15); }
  50% { background: rgba(233, 69, 96, 0.3); }
}
.clue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}
.clue-title {
  font-size: 14px;
  color: #eee;
  font-weight: bold;
}
.red-herring {
  font-size: 11px;
  color: #f39c12;
  margin-right: 8px;
}
.expand-icon {
  font-size: 11px;
  color: #888;
}
.clue-body {
  padding: 10px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.clue-hint {
  font-size: 12px;
  color: #888;
  margin: 0 0 6px 0;
  font-style: italic;
}
.clue-content {
  font-size: 13px;
  color: #ddd;
  line-height: 1.6;
  margin: 0;
}
</style>
