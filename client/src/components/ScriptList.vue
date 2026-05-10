<template>
  <div class="script-list">
    <div class="filters">
      <select v-model="filters.genre" @change="applyFilters" data-testid="genre-filter">
        <option value="">所有类型</option>
        <option value="悬疑推理">悬疑推理</option>
        <option value="古风权谋">古风权谋</option>
        <option value="现代都市">现代都市</option>
        <option value="恐怖惊悚">恐怖惊悚</option>
        <option value="欢乐搞笑">欢乐搞笑</option>
        <option value="科幻未来">科幻未来</option>
      </select>
      
      <select v-model="filters.difficulty" @change="applyFilters" data-testid="difficulty-filter">
        <option value="">所有难度</option>
        <option value="简单">简单</option>
        <option value="中等">中等</option>
        <option value="困难">困难</option>
      </select>
      
      <input 
        v-model="searchQuery" 
        @input="applyFilters"
        placeholder="搜索剧本标题..."
        class="search-input"
      />
    </div>

    <div class="scripts-grid">
      <div 
        v-for="script in filteredScripts" 
        :key="script.id"
        class="script-card"
        @click="$emit('select', script.id)"
      >
        <h3>{{ script.title }}</h3>
        <div class="meta">
          <span v-if="script.genre" class="genre">{{ script.genre }}</span>
          <span v-if="script.difficulty" class="difficulty">{{ script.difficulty }}</span>
          <span v-if="script.player_count" class="players">{{ script.player_count }}人</span>
          <span v-if="script.estimated_time" class="time">{{ script.estimated_time }}分钟</span>
        </div>
        <p class="description">{{ script.background_story?.substring(0, 100) }}...</p>
      </div>
    </div>

    <div v-if="filteredScripts.length === 0" class="empty-state">
      暂无剧本
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameStore } from '@/stores/game';
import type { ScriptFilters } from '@/types/script';

const store = useGameStore();
defineEmits<{ select: [scriptId: string] }>();

const filters = ref<ScriptFilters>({ genre: '', difficulty: '', min_players: 0 });
const searchQuery = ref('');

const filteredScripts = computed(() => {
  return store.availableScripts.filter((script) => {
    if (filters.value.genre && script.genre !== filters.value.genre) return false;
    if (filters.value.difficulty && script.difficulty !== filters.value.difficulty) return false;
    if (searchQuery.value && !script.title.includes(searchQuery.value)) return false;
    return true;
  });
});

function applyFilters() {
  // Local filtering via computed property - no API call needed
}


</script>

<style scoped>
.script-list {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filters select,
.search-input {
  padding: 8px 12px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #16213e;
  color: #eee;
  font-size: 14px;
}

.filters select:focus,
.search-input:focus {
  outline: none;
  border-color: #e94560;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #888;
}

.scripts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.script-card {
  border: 1px solid #444;
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  background: rgba(255, 255, 255, 0.05);
}

.script-card:hover {
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.2);
  transform: translateY(-2px);
}

.script-card h3 {
  font-size: 18px;
  color: #eee;
  margin: 0 0 10px 0;
}

.meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 10px 0;
}

.genre {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.difficulty {
  background: #fff3e0;
  color: #f57c00;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.players,
.time {
  color: #888;
  font-size: 12px;
}

.description {
  color: #888;
  font-size: 14px;
  margin-top: 10px;
  line-height: 1.5;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
  font-size: 16px;
}
</style>
