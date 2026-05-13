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
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: 80px;
  flex: 1;
  background: var(--bg-tertiary);
  min-height: 100vh;
}
</style>
