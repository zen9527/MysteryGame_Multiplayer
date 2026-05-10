<template>
  <div class="script-detail">
    <button @click="$emit('back')" class="back-btn">← 返回列表</button>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="script" class="content">
      <h1>{{ script.title }}</h1>
      
      <div class="meta">
        <span v-if="script.genre">类型：{{ script.genre }}</span>
        <span v-if="script.difficulty">难度：{{ script.difficulty }}</span>
        <span v-if="script.player_count">人数：{{ script.player_count }}人</span>
        <span v-if="script.estimated_time">时长：{{ script.estimated_time }}分钟</span>
      </div>

      <section class="background">
        <h2>背景故事</h2>
        <p>{{ script.background_story }}</p>
      </section>

      <section class="roles">
        <h2>角色列表</h2>
        <div v-for="role in script.roles" :key="role.id" class="role-card">
          <h3>{{ role.name }}</h3>
          <p><strong>年龄：</strong>{{ role.age }}</p>
          <p><strong>职业：</strong>{{ role.occupation }}</p>
          <p><strong>描述：</strong>{{ role.description }}</p>
        </div>
      </section>

      <section class="plot-outline">
        <h2>剧情大纲</h2>
        <div v-if="script.plot_outline">
          <div class="act"><strong>第一幕：</strong>{{ script.plot_outline.act1 }}</div>
          <div class="act"><strong>第二幕：</strong>{{ script.plot_outline.act2 }}</div>
          <div class="act"><strong>第三幕：</strong>{{ script.plot_outline.act3 }}</div>
        </div>
      </section>

      <div class="warning">
        ⚠️ 凶手身份、线索和私信事件将在游戏开始后揭晓
      </div>

      <button @click="$emit('start')" class="start-btn">开始游戏</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { scriptApi } from '@/types/script';
import type { ScriptDetail } from '@/types/script';

const props = defineProps<{ scriptId: string }>();
const emit = defineEmits(['back', 'start']);

const script = ref<ScriptDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    script.value = await scriptApi.getDetail(props.scriptId);
  } catch (e) {
    error.value = '加载剧本失败';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.script-detail { padding: 20px; max-width: 800px; margin: 0 auto; }
.back-btn { background: none; border: none; color: #666; cursor: pointer; margin-bottom: 20px; font-size: 16px; }
.back-btn:hover { color: #333; }
.loading { text-align: center; padding: 40px; color: #666; }
.error { text-align: center; padding: 40px; color: #f44336; }
.content { background: #fff; border-radius: 8px; }
h1 { margin: 0 0 20px 0; color: #333; }
.meta { display: flex; gap: 16px; margin: 20px 0; color: #666; flex-wrap: wrap; }
section { margin: 30px 0; }
h2 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }
.background p { line-height: 1.8; color: #555; }
.role-card { border: 1px solid #eee; padding: 15px; margin: 10px 0; border-radius: 8px; background: #fafafa; }
.role-card h3 { margin: 0 0 10px 0; color: #333; }
.role-card p { margin: 5px 0; color: #666; }
.act { padding: 10px 0; border-bottom: 1px solid #eee; }
.warning { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; color: #856404; }
.start-btn { background: #4caf50; color: white; border: none; padding: 12px 30px; 
             border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 20px; }
.start-btn:hover { background: #45a049; }
</style>
