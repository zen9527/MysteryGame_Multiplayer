<template>
  <div class="script-editor">
    <h3>📖 剧本预览</h3>

    <div v-if="!script" class="no-script">
      <p>尚未生成剧本。请先选择类型并点击"生成剧本"。</p>
    </div>

    <template v-else>
      <div class="script-header">
        <h2>{{ script.title }}</h2>
        <span class="genre-tag">{{ script.genre }}</span>
        <span class="difficulty-tag">{{ script.difficulty || '中等' }}</span>
      </div>

      <details open>
        <summary>背景故事</summary>
        <p class="script-text">{{ script.backgroundStory || script.background_story || '暂无' }}</p>
      </details>

      <details open>
        <summary>角色列表 ({{ roles?.length || 0 }}人)</summary>
        <div v-for="(role, i) in roles" :key="i" class="role-card">
          <strong>{{ role.name }}</strong> — {{ role.occupation }}，{{ role.age }}岁
          <p class="role-desc">{{ role.description || '' }}</p>
          <details>
            <summary>详细信息</summary>
            <p><strong>背景：</strong>{{ role.background }}</p>
            <p><strong>秘密任务：</strong>{{ role.secret_task }}</p>
            <p><strong>不在场证明：</strong>{{ role.alibi }}</p>
            <p><strong>动机：</strong>{{ role.motive }}</p>
          </details>
        </div>
      </details>

      <details>
        <summary>线索 ({{ clues?.length || 0 }}条)</summary>
        <div v-for="(clue, i) in clues" :key="i" class="clue-item">
          <strong>{{ clue.title }}</strong>: {{ clue.content }}
        </div>
      </details>

      <details>
        <summary>剧情大纲</summary>
        <p v-if="plotOutline"><strong>第一幕：</strong>{{ plotOutline.act1 }}</p>
        <p v-if="plotOutline"><strong>第二幕：</strong>{{ plotOutline.act2 }}</p>
        <p v-if="plotOutline"><strong>第三幕：</strong>{{ plotOutline.act3 }}</p>
      </details>

      <div class="script-actions">
        <button @click="$emit('confirm')" :disabled="!canConfirm" class="confirm-btn">
          ✅ 确认剧本，等待玩家加入
        </button>
        <button @click="$emit('regenerate')" class="regen-btn">🔄 重新生成</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  script: any | null;
}>();

defineEmits(['confirm', 'regenerate']);

const roles = computed(() => props.script?.roles || []);
const clues = computed(() => props.script?.clues || []);
const plotOutline = computed(() => props.script?.plot_outline || props.script?.plotOutline);
const canConfirm = computed(
  () => props.script && (props.script.roles?.length || 0) >= 2,
);
</script>

<style scoped>
.script-editor {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}
.script-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.script-header h2 {
  font-size: 18px;
  color: #eee;
}
.genre-tag, .difficulty-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.genre-tag { background: #e94560; color: #fff; }
.difficulty-tag { background: #0f3460; color: #eee; }
.script-text {
  line-height: 1.8;
  color: #ccc;
  padding: 8px 0;
}
.role-card {
  padding: 8px 12px;
  margin-bottom: 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
}
.role-desc { color: #aaa; font-size: 13px; }
.clue-item { padding: 4px 0; color: #bbb; }
details { margin-bottom: 8px; }
summary { cursor: pointer; color: #e94560; font-weight: bold; }
.script-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
.confirm-btn, .regen-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.confirm-btn { background: #27ae60; color: #fff; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.regen-btn { background: #333; color: #eee; }
.no-script { color: #888; padding: 24px; text-align: center; }
</style>
