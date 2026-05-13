<template>
  <div class="script-filter">
    <select v-model="localFilters.genre" @change="emitChange">
      <option value="">全部类型</option>
      <option value="悬疑推理">悬疑推理</option>
      <option value="古风权谋">古风权谋</option>
      <option value="现代都市">现代都市</option>
      <option value="恐怖惊悚">恐怖惊悚</option>
      <option value="欢乐搞笑">欢乐搞笑</option>
      <option value="科幻未来">科幻未来</option>
    </select>
    <select v-model="localFilters.difficulty" @change="emitChange">
      <option value="">全部难度</option>
      <option value="简单">简单</option>
      <option value="中等">中等</option>
      <option value="困难">困难</option>
    </select>
    <select v-model="localFilters.playerCount" @change="emitChange">
      <option value="">全部人数</option>
      <option value="3">3 人</option><option value="4">4 人</option>
      <option value="5">5 人</option><option value="6">6 人</option>
      <option value="7">7 人</option><option value="8">8 人</option>
    </select>
    <button @click="resetFilters" class="reset-btn">重置</button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
export interface FilterValues { genre: string; difficulty: string; playerCount: string; }
const props = defineProps<{ modelValue: FilterValues; }>();
const emit = defineEmits(['update:modelValue', 'change']);
const localFilters = ref<FilterValues>({ ...props.modelValue });
watch(localFilters, (newVal) => emit('update:modelValue', newVal), { deep: true });
function emitChange() { emit('change'); }
function resetFilters() { localFilters.value = { genre: '', difficulty: '', playerCount: '' }; emitChange(); }
</script>

<style scoped>
@import '../../styles/variables.css';
.script-filter { display: flex; gap: var(--space-md); padding: var(--space-lg); background: var(--bg-secondary); border-radius: var(--radius-lg); margin-bottom: var(--space-lg); }
select { padding: var(--space-sm) var(--space-md); border: 1px solid var(--border-medium); border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-primary); font-size: 14px; }
.reset-btn { padding: var(--space-sm) var(--space-lg); border: none; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); cursor: pointer; }
.reset-btn:hover { background: var(--hover-bg); color: var(--text-primary); }
</style>
