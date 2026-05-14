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
import { useRoute } from 'vue-router';

const route = useRoute();
</script>

<style>
#app {
  height: 100%;
  display: flex;
}

.main-content {
  /* Dynamic margin based on sidebar state */
  margin-left: calc(80px + (var(--sidebar-expanded, 0) * 160px));
  flex: 1;
  overflow-y: auto;
  transition: margin-left var(--transition-normal);
}
</style>
