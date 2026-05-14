<!-- client/src/components/common/CollapsibleSidebar.vue -->
<template>
  <aside 
    class="collapsible-sidebar" 
    :class="{ expanded: isExpanded }"
    @mouseenter="isExpanded = true"
    @mouseleave="isExpanded = false"
  >
    <div class="sidebar-header">
      <div class="logo">🎭</div>
    </div>
    
    <nav class="nav-items">
      <router-link 
        v-for="item in navItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="text" v-if="isExpanded">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const isExpanded = ref(false);

// Watch sidebar state and update CSS variable on body
watch(isExpanded, (expanded) => {
  document.body.style.setProperty('--sidebar-expanded', expanded ? '1' : '0');
}, { immediate: true });

const navItems = [
  { path: '/', icon: '🏠', label: '房间列表' },
  { path: '/scripts', icon: '📚', label: '剧本中心' },
  { path: '/create', icon: '➕', label: '创建房间' },
  { path: '/settings', icon: '⚙️', label: 'LLM 配置' },
];

function isActive(path: string) {
  return route.path === path || (path !== '/' && route.path.startsWith(path));
}
</script>

<style scoped>
@import '../../styles/variables.css';

.collapsible-sidebar {
  width: 80px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-medium);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.collapsible-sidebar.expanded {
  width: 240px;
}

.sidebar-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-medium);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo {
  font-size: 32px;
}

.nav-items {
  flex: 1;
  padding: var(--space-md) 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.nav-item:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--active-bg);
  color: var(--accent-primary);
  border-left: 3px solid var(--accent-primary);
}

.icon {
  font-size: 20px;
  min-width: 40px;
  text-align: center;
}

.text {
  margin-left: var(--space-md);
  white-space: nowrap;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.collapsible-sidebar.expanded .text {
  opacity: 1;
}
</style>
