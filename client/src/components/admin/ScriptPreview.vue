<script setup lang="ts">
// Script preview component - moved from ScriptEditor.vue
// This displays the generated script for admin review
</script>

<template>
  <div class="script-preview">
    <h2>📖 剧本预览</h2>
    <div class="preview-content">
      <!-- Script content would be displayed here -->
      <p>剧本功能待实现...</p>
    </div>
  </div>
</template>

<style scoped>
.script-preview {
  padding: 15px;
}

h2 {
  margin-bottom: 12px;
}

.preview-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  max-height: 400px;
  overflow-y: auto;
}

pre {
  white-space: pre-wrap;
  font-size: 0.9em;
  line-height: 1.6;
}
</style>
