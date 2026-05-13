<!-- client/src/components/common/CollapsibleSidebar.vue -->
<template>
  <aside class="collapsible-sidebar">
    <div class="logo-section">
      <div class="logo">🎭</div>
    </div>
    
    <nav class="nav-section">
      <div 
        v-for="item in navItems" 
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="navigate(item.path)"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="text">{{ item.label }}</span>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

interface NavItem {
  icon: string;
  label: string;
  path: string;
}

const navItems = computed<NavItem[]>(() => [
  { icon: '🏠', label: '房间列表', path: '/' },
  { icon: '📚', label: '剧本中心', path: '/scripts' },
  { icon: '⚙️', label: 'LLM 配置', path: '/settings' }
]);

function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/');
}

function navigate(path: string): void {
  router.push(path);
}
</script>

<style scoped>
@import '../../styles/variables.css';

.collapsible-sidebar {
  width: 80px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-light);
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: var(--space-xl) 0;
  transition: width var(--transition-normal);
  overflow: hidden;
  position: fixed;
  left: 0;
  top: 0;
}

.collapsible-sidebar:hover {
  width: 240px;
}

.logo-section {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-3xl);
}

.logo {
  font-size: 28px;
  filter: drop-shadow(0 0 10px rgba(121, 192, 255, 0.5));
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: 0 var(--space-lg);
}

.nav-item {
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--active-bg);
  color: var(--accent-primary);
}

.nav-item .icon {
  font-size: 20px;
  margin-right: var(--space-lg);
  min-width: 28px;
}

.nav-item .text {
  opacity: 0;
  transition: opacity var(--transition-fast);
  font-weight: 500;
  font-size: 13px;
}

.collapsible-sidebar:hover .nav-item .text {
  opacity: 1;
}
</style>
