<template>
  <div class="placeholder-page">
    <h1>🚧 功能开发中</h1>
    <p>剧本生成向导即将上线</p>
    <router-link to="/scripts" class="back-btn">返回剧本中心</router-link>
  </div>
</template>

<style scoped>
@import '../../styles/variables.css';
.placeholder-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 80px);
  text-align: center;
}
h1 { font-size: 32px; color: var(--text-primary); margin-bottom: var(--space-md); }
p { font-size: 16px; color: var(--text-secondary); margin-bottom: var(--space-xl); }
.back-btn {
  padding: var(--space-md) var(--space-xl);
  background: var(--accent-primary);
  color: var(--bg-primary);
  border-radius: var(--radius-md);
  text-decoration: none;
  font-weight: 600;
}
</style>
