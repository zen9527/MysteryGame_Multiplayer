import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ScriptDetail } from '@/types/script';

const API_BASE = '/api/scripts';

export interface GenerationFormData {
  genre: string;
  difficulty: string;
  playerCount: number;
}

export const useScriptGeneratorStore = defineStore('scriptGenerator', () => {
  // State
  const currentStep = ref(1);
  const formData = ref<GenerationFormData>({
    genre: '',
    difficulty: '',
    playerCount: 4,
  });
  const generating = ref(false);
  const generationStatus = ref('');
  const generatedScript = ref<ScriptDetail | null>(null);
  const error = ref<string | null>(null);

  // Constants
  const genres = ['悬疑推理', '古风权谋', '现代都市', '恐怖惊悚', '欢乐搞笑', '科幻未来'];
  const difficulties = ['简单', '中等', '困难'];
  const steps = [1, 2, 3, 4, 5];

  // Computed
  const canProceed = computed(() => {
    if (currentStep.value === 1) return formData.value.genre !== '';
    if (currentStep.value === 2) return formData.value.difficulty !== '';
    if (currentStep.value === 3) return true;
    if (currentStep.value === 4) return generatedScript.value !== null;
    return false;
  });

  const currentStepLabel = computed(() => {
    const labels: Record<number, string> = {
      1: '选择类型',
      2: '选择难度',
      3: '设置人数',
      4: '生成中',
      5: '确认',
    };
    return labels[currentStep.value];
  });

  // Actions
  function updateFormData(partial: Partial<GenerationFormData>) {
    formData.value = { ...formData.value, ...partial };
  }

  function selectGenre(genre: string) {
    formData.value.genre = genre;
  }

  function selectDifficulty(difficulty: string) {
    formData.value.difficulty = difficulty;
  }

  function setPlayerCount(count: number) {
    formData.value.playerCount = Math.max(3, Math.min(8, count));
  }

  async function generateScript() {
    generating.value = true;
    generationStatus.value = '正在连接 LLM...';
    error.value = null;
    
    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          genre: formData.value.genre,
          difficulty: formData.value.difficulty,
          player_count: formData.value.playerCount,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Generation failed: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('ReadableStream not supported');
      }
      
      const decoder = new TextDecoder();
      let accumulated = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        accumulated += chunk;
        generationStatus.value = '正在生成剧本...';
      }
      
      // Parse final JSON from SSE data
      const jsonMatch = accumulated.match(/data:\s*(\{.*\})/s);
      if (jsonMatch && jsonMatch[1]) {
        generatedScript.value = JSON.parse(jsonMatch[1]);
      } else {
        throw new Error('Failed to parse generated script');
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误';
      generationStatus.value = '生成失败';
      throw err;
    } finally {
      generating.value = false;
    }
  }

  function nextStep() {
    if (currentStep.value < 5) {
      currentStep.value++;
    }
  }

  function prevStep() {
    if (currentStep.value > 1) {
      currentStep.value--;
    }
  }

  function reset() {
    currentStep.value = 1;
    formData.value = { genre: '', difficulty: '', playerCount: 4 };
    generatedScript.value = null;
    error.value = null;
  }

  return {
    // State
    currentStep,
    formData,
    generating,
    generationStatus,
    generatedScript,
    error,
    genres,
    difficulties,
    steps,
    // Computed
    canProceed,
    currentStepLabel,
    // Actions
    updateFormData,
    selectGenre,
    selectDifficulty,
    setPlayerCount,
    generateScript,
    nextStep,
    prevStep,
    reset,
  };
});
