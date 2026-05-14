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

      <!-- Step 3: Player Count + Generation -->
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
        
        <!-- Generation Section (shown after clicking "生成剧本") -->
        <div v-if="store.generating || store.generatedScript || store.error" class="generation-section">
          <h3>剧本生成</h3>
          
          <!-- Loading State -->
          <div v-if="store.generating" class="generation-status">
            <div class="spinner"></div>
            <p>{{ store.generationStatus }}</p>
          </div>
          
          <!-- Success Preview -->
          <div v-if="store.generatedScript && !store.error" class="preview-panel">
            <h4>生成结果预览</h4>
            <div class="script-preview">
              <h5>{{ store.generatedScript.title }}</h5>
              <p class="meta">
                {{ store.generatedScript.genre }} · 
                {{ store.generatedScript.difficulty }} · 
                {{ store.generatedScript.player_count }}人
              </p>
              <p v-if="store.generatedScript.background_story" class="preview-text">
                {{ store.generatedScript.background_story?.slice(0, 200) }}...
              </p>
            </div>
          </div>
          
          <!-- Error State -->
          <div v-if="store.error" class="error-message">
            ⚠️ {{ store.error }}
            <button @click="retryGeneration" class="retry-btn">重试生成</button>
          </div>
        </div>
      </div>

      <!-- Step 4: Preview -->
      <div v-if="store.currentStep === 4" class="step-content">
        <h2>剧本预览</h2>
        <div class="preview-panel">
          <div class="script-preview">
            <h3>{{ store.generatedScript?.title }}</h3>
            <p class="meta">
              {{ store.generatedScript?.genre }} · 
              {{ store.generatedScript?.difficulty }} · 
              {{ store.generatedScript?.player_count }}人
            </p>
            <p v-if="store.generatedScript?.background_story" class="preview-text">
              {{ store.generatedScript.background_story?.slice(0, 400) }}...
            </p>
          </div>
        </div>
      </div>

      <!-- Step 5: Confirmation -->
      <div v-if="store.currentStep === 5" class="step-content">
        <h2>确认剧本</h2>
        <div class="final-preview">
          <div class="script-card">
            <h3>{{ store.generatedScript?.title }}</h3>
            <div class="meta">
              <span>{{ store.generatedScript?.genre }}</span>
              <span>{{ store.generatedScript?.difficulty }}</span>
              <span>{{ store.generatedScript?.player_count }}人</span>
            </div>
            <p v-if="store.generatedScript?.background_story" class="description">
              {{ store.generatedScript.background_story.slice(0, 300) }}...
            </p>
            <div v-if="store.generatedScript?.roles" class="roles-preview">
              <h4>角色列表</h4>
              <ul>
                <li v-for="(role, index) in store.generatedScript.roles.slice(0, 5)" :key="index">
                  {{ role.name }} - {{ role.occupation }}
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <div class="wizard-actions">
          <button @click="confirmScript" class="confirm-btn">
            ✅ 确认并保存
          </button>
          <button @click="regenerate" class="regen-btn">
            🔄 重新生成
          </button>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <div class="wizard-nav" v-if="store.currentStep < 5">
      <button @click="store.prevStep" :disabled="store.currentStep === 1">← 上一步</button>
      <button 
        @click="handleNext" 
        :disabled="!store.canProceed || store.generating"
      >
        {{ getButtonText() }}
      </button>
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
import { useRouter } from 'vue-router';

const store = useScriptGeneratorStore();
const router = useRouter();
const playerCountInput = ref(store.formData.playerCount);

function updatePlayerCount() {
  store.setPlayerCount(playerCountInput.value);
}

function getButtonText(): string {
  if (store.generating) return '生成中...';
  if (store.currentStep === 3) {
    if (store.error) return '🔄 重试生成';
    if (store.generatedScript) return '下一步 →';
    return '生成剧本 →';
  }
  return '下一步 →';
}

async function handleNext() {
  if (!store.canProceed) return;
  
  if (store.currentStep === 3 && !store.generatedScript) {
    // Step 3: First time clicking "下一步" - start generation
    await store.generateScript();
    
    // Check if generation succeeded
    if (store.error || !store.generatedScript) {
      console.error('Script generation failed:', store.error);
      // Stay on step 3, don't proceed
      return;
    }
    
    // Generation succeeded, move to step 4 (preview)
    store.nextStep();
  } else {
    // Other steps: just proceed
    store.nextStep();
  }
}

function retryGeneration() {
  store.generateScript();
}

async function confirmScript() {
  if (!store.generatedScript) return;
  
  // TODO: Save script to backend (if needed)
  // For now, just redirect to scripts list
  router.push('/scripts');
}

function regenerate() {
  store.reset();
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

/* Step 5 - Final Preview */
.final-preview {
  margin-bottom: var(--space-xl);
}

.script-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.script-card h3 {
  font-size: 28px;
  color: var(--accent-primary);
  margin-bottom: var(--space-md);
}

.script-card .meta {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.script-card .meta span {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

.script-card .description {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: var(--space-lg);
}

.roles-preview h4 {
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
}

.roles-preview ul {
  list-style: none;
  padding: 0;
  display: grid;
  gap: var(--space-sm);
}

.roles-preview li {
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

/* Wizard Actions */
.wizard-actions {
  display: flex;
  justify-content: center;
  gap: var(--space-lg);
  margin-top: var(--space-xl);
}

.confirm-btn, .regen-btn {
  padding: var(--space-lg) var(--space-2xl);
  font-size: 18px;
  font-weight: 600;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.confirm-btn {
  background: var(--success);
  border: 2px solid var(--success);
  color: var(--bg-primary);
}

.confirm-btn:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}

.regen-btn {
  background: var(--bg-tertiary);
  border: 2px solid var(--border-medium);
  color: var(--text-primary);
}

.regen-btn:hover {
  background: var(--hover-bg);
}
</style>
