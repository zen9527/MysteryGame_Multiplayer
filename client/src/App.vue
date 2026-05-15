<!-- client/src/App.vue -->
<template>
  <div id="app">
    <CollapsibleSidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import CollapsibleSidebar from './components/common/CollapsibleSidebar.vue';
</script>

<style>
@import './styles/variables.css';

#app {
  height: 100%;
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: calc(80px + (var(--sidebar-expanded, 0) * 160px));
  flex: 1;
  overflow-y: auto;
  transition: margin-left var(--transition-normal);
  background: var(--bg-tertiary);
  min-height: 100vh;
}
</style>
