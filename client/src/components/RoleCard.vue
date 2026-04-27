<template>
  <div class="role-card">
    <div v-if="!hasLayer1" class="no-role">
      <p>等待剧本生成...</p>
    </div>
    <div v-else class="card-content">
      <!-- Layer 1: Always visible -->
      <div class="card-header">
        <h3 class="role-name">{{ layer1?.name }}</h3>
        <p class="role-desc">{{ layer1?.description }}</p>
      </div>

      <!-- Layer 2: Unlocked at act1 -->
      <div v-if="layer2" class="card-section">
        <div class="section-header" @click="toggleSection('layer2')">
          <span>📖 背景故事</span>
          <span class="expand-icon">{{ expandedSections.layer2 ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.layer2" class="section-body">
          <p>{{ layer2.background }}</p>
        </div>

        <div class="section-header" @click="toggleSection('secret_task')">
          <span>🎯 秘密任务</span>
          <span class="expand-icon">{{ expandedSections.secret_task ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.secret_task" class="section-body">
          <p>{{ layer2.secret_task }}</p>
        </div>

        <div class="section-header" @click="toggleSection('alibi')">
          <span>🛡️ 不在场证明</span>
          <span class="expand-icon">{{ expandedSections.alibi ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.alibi" class="section-body">
          <p>{{ layer2.alibi }}</p>
        </div>
      </div>

      <!-- Layer 3: Unlocked at act2 -->
      <div v-if="layer3" class="card-section">
        <div class="section-header" @click="toggleSection('relationships')">
          <span>🤝 人际关系</span>
          <span class="expand-icon">{{ expandedSections.relationships ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.relationships" class="section-body">
          <ul v-if="layer3.relationships?.length">
            <li v-for="(rel, i) in layer3.relationships" :key="i">
              <strong>{{ rel.target }}</strong>: {{ rel.description }}
            </li>
          </ul>
          <p v-else class="no-relations">暂无人际关系信息</p>
        </div>

        <div class="section-header" @click="toggleSection('motive')">
          <span>💡 动机</span>
          <span class="expand-icon">{{ expandedSections.motive ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.motive" class="section-body">
          <p>{{ layer3.motive }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameStore } from '../stores/game';

const store = useGameStore();

const expandedSections = ref<Record<string, boolean>>({
  layer2: true,
  secret_task: true,
  alibi: true,
  relationships: true,
  motive: true,
});

const layer1 = computed(() => store.roleCard.layer1);
const layer2 = computed(() => store.roleCard.layer2);
const layer3 = computed(() => store.roleCard.layer3);
const hasLayer1 = computed(() => !!layer1.value);

function toggleSection(section: string) {
  expandedSections.value[section] = !expandedSections.value[section];
}
</script>

<style scoped>
.role-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
}
.no-role {
  text-align: center;
  color: #666;
  padding: 24px;
}
.card-header {
  text-align: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 12px;
}
.role-name {
  font-size: 20px;
  color: #e94560;
  margin: 0 0 4px 0;
}
.role-desc {
  font-size: 13px;
  color: #aaa;
  margin: 0;
}
.card-section {
  margin-bottom: 12px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  cursor: pointer;
  color: #ccc;
  font-size: 14px;
  user-select: none;
}
.section-header:hover {
  background: rgba(0, 0, 0, 0.3);
}
.expand-icon {
  font-size: 11px;
  color: #888;
}
.section-body {
  padding: 10px 12px;
  color: #ddd;
  font-size: 13px;
  line-height: 1.6;
}
.section-body p {
  margin: 0;
}
.section-body ul {
  margin: 0;
  padding-left: 20px;
}
.section-body li {
  margin-bottom: 6px;
}
.no-relations {
  color: #666;
  font-style: italic;
}
</style>
