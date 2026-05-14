import { describe, it, expect } from 'vitest';
import { createTestingPinia } from '@pinia/testing';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';

describe('ScriptGenerator Store', () => {
  beforeEach(() => {
    createTestingPinia({
      stubActions: false,
      createSpy: vi.fn,
    });
  });

  it('initializes with default state', () => {
    const store = useScriptGeneratorStore();
    expect(store.currentStep).toBe(1);
    expect(store.generating).toBe(false);
    expect(store.generatedScript).toBeNull();
    expect(store.formData).toEqual({ genre: '', difficulty: '', playerCount: 4 });
    expect(store.error).toBeNull();
  });

  it('updates form data', () => {
    const store = useScriptGeneratorStore();
    store.updateFormData({ genre: '悬疑推理', difficulty: '中等', playerCount: 5 });
    expect(store.formData.genre).toBe('悬疑推理');
    expect(store.formData.difficulty).toBe('中等');
    expect(store.formData.playerCount).toBe(5);
  });

  it('validates form for each step', () => {
    const store = useScriptGeneratorStore();
    
    // Step 1: requires genre
    expect(store.currentStep).toBe(1);
    expect(store.canProceed).toBe(false);
    
    store.updateFormData({ genre: '悬疑推理' });
    expect(store.canProceed).toBe(true);
    
    // Use nextStep to change currentStep
    store.nextStep();
    expect(store.currentStep).toBe(2);
    expect(store.canProceed).toBe(false);
    
    store.updateFormData({ difficulty: '中等' });
    expect(store.canProceed).toBe(true);
    
    store.nextStep();
    expect(store.currentStep).toBe(3);
    // Step 3: requires generatedScript (not just form data)
    expect(store.canProceed).toBe(false);
    
    // Simulate successful generation
    store.generatedScript = { id: 'test', title: 'Test' } as any;
    expect(store.canProceed).toBe(true);
  });
});
