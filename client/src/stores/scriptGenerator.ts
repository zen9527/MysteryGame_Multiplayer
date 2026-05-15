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
  
  // Progress tracking
  const currentProgressStep = ref(1);
  const totalProgressSteps = ref(5);
  const progressPercent = ref(0);

  // Constants
  const genres = ['悬疑推理', '古风权谋', '现代都市', '恐怖惊悚', '欢乐搞笑', '科幻未来'];
  const difficulties = ['简单', '中等', '困难'];
  const steps = [1, 2, 3, 4, 5];
  
  // Progress steps definition
  const progressSteps = [
    { name: '构建提示词' },
    { name: '调用 AI' },
    { name: '生成内容' },
    { name: '解析验证' },
    { name: '完成' },
  ];

  // Computed
  const canProceed = computed(() => {
    if (currentStep.value === 1) return formData.value.genre !== '';
    if (currentStep.value === 2) return formData.value.difficulty !== '';
    if (currentStep.value === 3) return true; // Step 3: always allow clicking to trigger generation
    if (currentStep.value === 4) return generatedScript.value !== null;
    return false;
  });

  const currentStepLabel = computed(() => {
    const labels: Record<number, string> = {
      1: '选择类型',
      2: '选择难度',
      3: '设置人数并生成',
      4: '预览',
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

  let currentAbortController: AbortController | null = null;
  let isCancelled = ref(false);

  async function generateScript(signal?: AbortSignal) {
    // Create a new abort controller for this request
    currentAbortController = new AbortController();
    const effectiveSignal = signal ?? currentAbortController.signal;
    
    generating.value = true;
    generationStatus.value = '正在连接 LLM...';
    error.value = null;
    isCancelled.value = false;
    currentProgressStep.value = 1;
    totalProgressSteps.value = 5;
    progressPercent.value = 0;
    
    let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
    
    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          genre: formData.value.genre,
          difficulty: formData.value.difficulty,
          player_count: formData.value.playerCount,
          estimated_time: 90, // Default value
        }),
        signal: effectiveSignal,
      });
      
      if (!response.ok) {
        error.value = `Generation failed: ${response.status}`;
        generationStatus.value = '生成失败';
        return;
      }
      
      reader = response.body?.getReader() ?? null;
      if (!reader) {
        error.value = 'ReadableStream not supported';
        generationStatus.value = '生成失败';
        return;
      }
      
      const decoder = new TextDecoder();
      let buffer = '';
      let lastDataEvent: { type: string; data?: any; message?: string } | null = null;
      
      while (true) {
        // Check if cancelled before reading
        if (isCancelled.value) {
          console.log('Generation cancelled by user');
          break;
        }
        
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        buffer += chunk;
        
        // Process complete SSE events
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep incomplete event in buffer
        
        for (const event of events) {
          if (event.startsWith('data:')) {
            try {
              const data = JSON.parse(event.slice(5).trim());
              
              // Handle different event types
              if (data.type === 'status') {
                currentProgressStep.value = data.step;
                totalProgressSteps.value = data.total_steps;
                generationStatus.value = data.message;
                
                // Calculate progress percentage based on step
                if (data.step === 5) {
                  progressPercent.value = 100;
                } else if (data.step === 3 && data.message) {
                  // Step 3: backend sends actual progress percentage in message like "正在生成...(45%)"
                  const match = data.message.match(/\((\d+)%\)/);
                  if (match) {
                    progressPercent.value = parseInt(match[1], 10);
                  } else {
                    progressPercent.value = Math.round((data.step / data.total_steps) * 90);
                  }
                } else {
                  progressPercent.value = Math.round((data.step / data.total_steps) * 90);
                }
              } else if (data.type === 'chunk') {
                // Advance to step 3 on first chunk if not already there
                if (currentProgressStep.value < 3) {
                  currentProgressStep.value = 3;
                  progressPercent.value = 40;
                }
                generationStatus.value = '正在生成剧本内容...';
              } else if (data.type === 'start') {
                generationStatus.value = '开始生成...';
              } else if (data.type === 'error') {
                error.value = data.message || '生成失败';
                generationStatus.value = '生成失败';
                return;
              } else if (data.type === 'done') {
                lastDataEvent = data;
              }
            } catch (e) {
              // Skip invalid JSON
              continue;
            }
          }
        }
      }
      
      // If cancelled, exit early
      if (isCancelled.value) {
        generationStatus.value = '已取消';
        return;
      }
      
      if (!lastDataEvent || lastDataEvent.type !== 'done') {
        error.value = 'No valid completion event found in SSE response';
        generationStatus.value = '生成失败';
        return;
      }
      
      try {
        generatedScript.value = lastDataEvent.data;
      } catch (parseError) {
        error.value = `Failed to parse generated script: ${parseError instanceof Error ? parseError.message : 'Unknown error'}`;
        generationStatus.value = '生成失败';
        return;
      }
    } catch (err) {
      // Handle abort/cancellation gracefully
      if (isCancelled.value || (err instanceof Error && err.name === 'AbortError')) {
        // Request was cancelled, don't show error
        console.log('Generation cancelled');
        generationStatus.value = '已取消';
      } else {
        error.value = err instanceof Error ? err.message : '未知错误';
        generationStatus.value = '生成失败';
        console.error('Generation error:', err);
      }
    } finally {
      generating.value = false;
      currentAbortController = null;
      isCancelled.value = false;
      if (reader) {
        try {
          await reader.cancel();
        } catch (e) {
          // Ignore cancel errors in finally block
        }
      }
    }
  }

  function cancelRequest() {
    if (currentAbortController) {
      isCancelled.value = true;
      currentAbortController.abort();
      currentAbortController = null;
      console.log('Generation cancelled by user');
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
    progressSteps,
    currentProgressStep,
    totalProgressSteps,
    progressPercent,
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
    cancelRequest,
    nextStep,
    prevStep,
    reset,
  };
});
