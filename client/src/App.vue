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
/* App-level styles - most moved to global.css */
#app {
  height: 100%;
  display: flex;
}

.main-content {
  margin-left: 80px;
  flex: 1;
  overflow-y: auto;
  transition: margin-left var(--transition-normal);
}

/* When sidebar is expanded via hover, main content doesn't move */
/* This keeps the layout stable during hover interactions */
</style>
