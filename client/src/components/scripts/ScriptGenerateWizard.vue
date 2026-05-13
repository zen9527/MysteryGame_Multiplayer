<template>
  <div class="script-wizard">
    <!-- Header with progress indicator -->
    <header class="wizard-header">
      <h1>🎭 生成新剧本</h1>
      <div class="progress-indicator">
        <span v-for="step in store.steps" :key="step" :class="{ 
          active: step === store.currentStep,
          completed: step < store.currentStep
        }">{{ step }}</span>
      </div>
      <p class="step-label">{{ store.currentStepLabel }}</p>
    </header>

    <!-- Step Content -->
    <div class="wizard-content">
      <!-- Step 1: Genre Selection -->
      <div v-if="store.currentStep === 1" class="step-content">
        <h2>选择剧本类型</h2>
        <div class="genre-grid">
          <button 
            v-for="genre in store.genres" 
            :key="genre"
            @click="store.selectGenre(genre)" 
            :class="{ selected: store.formData.genre === genre }"
          >
            {{ genre }}
          </button>
        </div>
      </div>

      <!-- Step 2: Difficulty Selection -->
      <div v-if="store.currentStep === 2" class="step-content">
        <h2>选择难度</h2>
        <div class="difficulty-options">
          <button 
            v-for="diff in store.difficulties" 
            :key="diff"
            @click="store.selectDifficulty(diff)" 
            :class="{ selected: store.formData.difficulty === diff }"
          >
            {{ diff }}
          </button>
        </div>
      </div>

      <!-- Step 3: Player Count -->
      <div v-if="store.currentStep === 3" class="step-content">
        <h2>玩家数量</h2>
        <div class="slider-container">
          <input 
            type="range" 
            v-model.number="playerCountInput" 
            min="3" 
            max="8" 
            @input="updatePlayerCount" 
          />
          <div class="player-display">{{ store.formData.playerCount }} 人</div>
        </div>
      </div>

      <!-- Step 4: Generation -->
      <div v-if="store.currentStep === 4" class="step-content">
        <h2>正在生成剧本...</h2>
        
        <!-- Loading State -->
        <div v-if="store.generating" class="generation-status">
          <div class="spinner"></div>
          <p>{{ store.generationStatus }}</p>
        </div>
        
        <!-- Success Preview -->
        <div v-if="store.generatedScript" class="preview-panel">
          <h3>生成结果预览</h3>
          <div class="script-preview">
            <h4>{{ store.generatedScript.title }}</h4>
            <p class="meta">
              {{ store.generatedScript.genre }} · 
              {{ store.generatedScript.difficulty }} · 
              {{ store.generatedScript.player_count }}人
            </p>
            <p v-if="store.generatedScript.background_story" class="preview-text">
              {{ store.generatedScript.background_story.slice(0, 200) }}...
            </p>
          </div>
        </div>
        
        <!-- Error State -->
        <div v-if="store.error" class="error-message">
          ⚠️ {{ store.error }}
          <button @click="retryGeneration" class="retry-btn">重试</button>
        </div>
      </div>

      <!-- Step 5: Confirmation Placeholder -->
      <div v-if="store.currentStep === 5" class="step-content">
        <p>确认功能待实现...</p>
      </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-nav" v-if="store.currentStep < 5">
      <button @click="store.prevStep" :disabled="store.currentStep === 1">← 上一步</button>
      <button @click="handleNext" :disabled="!store.canProceed">下一步 →</button>
    </div>

    <!-- Cancel Button -->
    <div class="wizard-footer">
      <router-link to="/scripts" class="cancel-btn">取消</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';

const store = useScriptGeneratorStore();
const playerCountInput = ref(store.formData.playerCount);

function updatePlayerCount() {
  store.setPlayerCount(playerCountInput.value);
}

async function handleNext() {
  if (!store.canProceed) return;
  
  if (store.currentStep === 3) {
    try {
      await store.generateScript();
    } catch (error) {
      // Error already set in store, don't proceed
      return;
    }
  }
  
  store.nextStep();
}

function retryGeneration() {
  store.generateScript();
}
</script>

<style scoped>
@import '../../styles/variables.css';

.script-wizard {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-2xl);
}

/* Header */
.wizard-header {
  text-align: center;
  margin-bottom: var(--space-3xl);
}

.wizard-header h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin-bottom: var(--space-xl);
}

/* Progress Indicator */
.progress-indicator {
  display: flex;
  justify-content: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.progress-indicator span {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-round);
  background: var(--bg-secondary);
  border: 2px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-weight: 600;
  transition: all var(--transition-fast);
}

.progress-indicator span.active {
  border-color: var(--accent-primary);
  background: var(--active-bg);
  color: var(--accent-primary);
}

.progress-indicator span.completed {
  border-color: var(--accent-primary);
  background: var(--accent-primary);
  color: var(--bg-primary);
}

.step-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* Step Content */
.wizard-content {
  min-height: 300px;
}

.step-content h2 {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: var(--space-xl);
  text-align: center;
}

/* Genre Grid */
.genre-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.genre-grid button {
  padding: var(--space-xl) var(--space-lg);
  background: var(--bg-secondary);
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.genre-grid button:hover {
  border-color: var(--border-accent);
  background: var(--hover-bg);
}

.genre-grid button.selected {
  border-color: var(--accent-primary);
  background: var(--active-bg);
  color: var(--accent-primary);
}

/* Difficulty Options */
.difficulty-options {
  display: flex;
  justify-content: center;
  gap: var(--space-lg);
}

.difficulty-options button {
  padding: var(--space-lg) var(--space-2xl);
  background: var(--bg-secondary);
  border: 2px solid var(--border-light);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.difficulty-options button:hover {
  border-color: var(--border-accent);
  background: var(--hover-bg);
}

.difficulty-options button.selected {
  border-color: var(--accent-primary);
  background: var(--active-bg);
  color: var(--accent-primary);
}

/* Slider */
.slider-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xl);
}

.slider-container input[type="range"] {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-round);
  outline: none;
  -webkit-appearance: none;
}

.slider-container input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  background: var(--accent-primary);
  border-radius: var(--radius-round);
  cursor: pointer;
}

.player-display {
  font-size: 32px;
  color: var(--accent-primary);
  font-weight: 700;
}

/* Navigation */
.wizard-nav {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-2xl);
  gap: var(--space-lg);
}

.wizard-nav button {
  padding: var(--space-md) var(--space-xl);
  background: var(--bg-secondary);
  border: 2px solid var(--border-medium);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-width: 120px;
}

.wizard-nav button:hover:not(:disabled) {
  border-color: var(--accent-primary);
  background: var(--hover-bg);
}

.wizard-nav button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.wizard-nav button:last-child {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: var(--bg-primary);
}

.wizard-nav button:last-child:hover:not(:disabled) {
  opacity: 0.9;
}

/* Footer */
.wizard-footer {
  text-align: center;
  margin-top: var(--space-xl);
}

.cancel-btn {
  padding: var(--space-md) var(--space-xl);
  background: transparent;
  border: 2px solid var(--border-medium);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all var(--transition-fast);
}

.cancel-btn:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

/* Generation Status */
.generation-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-2xl);
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid var(--border-medium);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-panel {
  margin-top: var(--space-xl);
  padding: var(--space-lg);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-medium);
}

.preview-panel h3 {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.script-preview h4 {
  font-size: 24px;
  color: var(--accent-primary);
  margin-bottom: var(--space-sm);
}

.script-preview .meta {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.script-preview .preview-text {
  font-size: 16px;
  color: var(--text-primary);
  line-height: 1.6;
}

.error-message {
  background: var(--error-bg);
  border: 1px solid var(--error);
  color: var(--error);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.retry-btn {
  padding: var(--space-sm) var(--space-md);
  background: var(--error);
  color: var(--bg-primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 600;
}
</style>
