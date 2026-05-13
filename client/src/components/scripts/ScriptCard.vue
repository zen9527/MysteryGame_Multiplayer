<template>
  <div class="script-card" :class="{ active }">
    <div class="card-header"><h3>{{ script.title }}</h3><span class="genre-tag">{{ script.genre }}</span></div>
    <div class="card-meta">
      <span v-if="script.difficulty" class="difficulty-tag">{{ script.difficulty }}</span>
      <span v-if="script.player_count" class="player-tag">{{ script.player_count }}人</span>
      <span v-if="script.created_at" class="date-tag">{{ formatDate(script.created_at) }}</span>
    </div>
    <p v-if="script.description" class="card-desc">{{ truncate(script.description, 100) }}</p>
    <p v-else-if="script.background_story" class="card-desc">{{ truncate(script.background_story, 100) }}</p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ script: { id: string; title: string; genre: string; difficulty?: string; player_count?: number; created_at?: string; description?: string; background_story?: string; }; active: boolean; }>();
function formatDate(date: string): string { return new Date(date).toLocaleDateString('zh-CN'); }
function truncate(text: string, length: number): string { return text.length > length ? text.slice(0, length) + '...' : text; }
</script>

<style scoped>
@import '../../styles/variables.css';
.script-card { background: var(--bg-secondary); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: var(--space-lg); cursor: pointer; transition: all var(--transition-fast); }
.script-card:hover { border-color: var(--border-accent); transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.script-card.active { border-color: var(--accent-primary); background: var(--active-bg); }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-md); }
.card-header h3 { font-size: 16px; color: var(--text-primary); margin: 0; }
.genre-tag { padding: var(--space-xs) var(--space-sm); background: var(--accent-secondary); color: var(--bg-primary); border-radius: var(--radius-sm); font-size: 12px; }
.card-meta { display: flex; gap: var(--space-sm); margin-bottom: var(--space-md); flex-wrap: wrap; }
.difficulty-tag, .player-tag, .date-tag { font-size: 12px; color: var(--text-secondary); }
.card-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin: 0; }
</style>
