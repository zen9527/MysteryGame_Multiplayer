import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import { createRouter, createWebHistory } from 'vue-router';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';
import ScriptGenerateWizard from '@/components/scripts/ScriptGenerateWizard.vue';

// Create a mock router for tests
const createMockRouter = () => {
  return createRouter({
    history: createWebHistory(),
    routes: [{ path: '/scripts', component: { template: '<div>Scripts</div>' } }],
  });
};

describe('ScriptGenerateWizard', () => {
  const mountComponent = (options?: { mocks?: Record<string, unknown> }) => {
    const router = createMockRouter();
    
    return mount(ScriptGenerateWizard, {
      global: {
        plugins: [
          createTestingPinia({
            stubActions: false,
          }),
          router,
        ],
        stubs: { 'router-link': true },
        ...(options?.mocks ? { mocks: options.mocks } : {}),
      },
    });
  };

  describe('Step 1 - Genre Selection', () => {
    it('renders step 1 genre selection', () => {
      const wrapper = mountComponent();
      
      expect(wrapper.find('h2').text()).toBe('选择剧本类型');
      expect(wrapper.findAll('.genre-grid button').length).toBe(6);
    });

    it('displays all genre options', () => {
      const wrapper = mountComponent();
      const buttons = wrapper.findAll('.genre-grid button');
      
      expect(buttons[0].text()).toBe('悬疑推理');
      expect(buttons[1].text()).toBe('古风权谋');
      expect(buttons[2].text()).toBe('现代都市');
      expect(buttons[3].text()).toBe('恐怖惊悚');
      expect(buttons[4].text()).toBe('欢乐搞笑');
      expect(buttons[5].text()).toBe('科幻未来');
    });

    it('highlights selected genre', async () => {
      const wrapper = mountComponent();
      const buttons = wrapper.findAll('.genre-grid button');
      
      // Initially no genre selected
      expect(buttons[0].classes()).not.toContain('selected');
      
      // Click first genre
      await buttons[0].trigger('click');
      
      // First button should be highlighted
      expect(buttons[0].classes()).toContain('selected');
      expect(buttons[1].classes()).not.toContain('selected');
    });
  });

  describe('Step 2 - Difficulty Selection', () => {
    it('renders step 2 difficulty selection when navigated', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2 by selecting a genre first
      const genreButton = wrapper.find('.genre-grid button');
      await genreButton.trigger('click');
      
      const nextButton = wrapper.find('.wizard-nav button:last-child');
      await nextButton.trigger('click');
      
      expect(wrapper.find('h2').text()).toBe('选择难度');
      expect(wrapper.findAll('.difficulty-options button').length).toBe(3);
    });

    it('displays all difficulty options', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const buttons = wrapper.findAll('.difficulty-options button');
      
      expect(buttons[0].text()).toBe('简单');
      expect(buttons[1].text()).toBe('中等');
      expect(buttons[2].text()).toBe('困难');
    });

    it('highlights selected difficulty', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const buttons = wrapper.findAll('.difficulty-options button');
      
      // Initially no difficulty selected
      expect(buttons[0].classes()).not.toContain('selected');
      
      // Click first difficulty
      await buttons[0].trigger('click');
      
      // First button should be highlighted
      expect(buttons[0].classes()).toContain('selected');
    });
  });

  describe('Step 3 - Player Count', () => {
    it('renders step 3 player count when navigated', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      // Navigate to step 3
      await wrapper.find('.difficulty-options button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      expect(wrapper.find('h2').text()).toBe('玩家数量');
      expect(wrapper.find('input[type="range"]').exists()).toBe(true);
    });

    it('shows player count slider with range 3-8', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 3
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      await wrapper.find('.difficulty-options button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const slider = wrapper.find('input[type="range"]');
      expect(slider.attributes('min')).toBe('3');
      expect(slider.attributes('max')).toBe('8');
    });

    it('updates player count via slider', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 3
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      await wrapper.find('.difficulty-options button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const slider = wrapper.find('input[type="range"]');
      await slider.setValue(6);
      
      expect(wrapper.find('.player-display').text()).toBe('6 人');
    });
  });

  describe('Progress Indicator', () => {
    it('shows progress indicator with all steps', () => {
      const wrapper = mountComponent();
      
      const indicators = wrapper.findAll('.progress-indicator span');
      expect(indicators.length).toBe(5);
    });

    it('highlights current step as active', () => {
      const wrapper = mountComponent();
      
      const indicators = wrapper.findAll('.progress-indicator span');
      expect(indicators[0].classes()).toContain('active');
      expect(indicators[1].classes()).not.toContain('active');
    });

    it('shows completed steps after navigation', async () => {
      const wrapper = mountComponent();
      
      // Complete step 1
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const indicators = wrapper.findAll('.progress-indicator span');
      expect(indicators[0].classes()).toContain('completed');
      expect(indicators[1].classes()).toContain('active');
    });

    it('shows current step label', () => {
      const wrapper = mountComponent();
      
      expect(wrapper.find('.step-label').text()).toBe('选择类型');
    });
  });

  describe('Navigation Buttons', () => {
    it('disables next button when form invalid (step 1)', () => {
      const wrapper = mountComponent();
      
      const nextButton = wrapper.find('.wizard-nav button:last-child');
      expect(nextButton.attributes('disabled')).toBeDefined();
    });

    it('enables next button when genre selected', async () => {
      const wrapper = mountComponent();
      
      await wrapper.find('.genre-grid button').trigger('click');
      
      const nextButton = wrapper.find('.wizard-nav button:last-child');
      expect(nextButton.attributes('disabled')).toBeUndefined();
    });

    it('disables next button when difficulty not selected (step 2)', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const nextButton = wrapper.find('.wizard-nav button:last-child');
      expect(nextButton.attributes('disabled')).toBeDefined();
    });

    it('enables next button when difficulty selected', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2 and select difficulty
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      await wrapper.find('.difficulty-options button').trigger('click');
      
      const nextButton = wrapper.find('.wizard-nav button:last-child');
      expect(nextButton.attributes('disabled')).toBeUndefined();
    });

    it('disables previous button on step 1', () => {
      const wrapper = mountComponent();
      
      const prevButton = wrapper.find('.wizard-nav button:first-child');
      expect(prevButton.attributes('disabled')).toBeDefined();
    });

    it('enables previous button on step 2', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 2
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      const prevButton = wrapper.find('.wizard-nav button:first-child');
      expect(prevButton.attributes('disabled')).toBeUndefined();
    });
  });

  describe('Cancel Button', () => {
    it('shows cancel button in footer', () => {
      const wrapper = mountComponent();
      
      expect(wrapper.find('.cancel-btn').exists()).toBe(true);
    });

    it('links to scripts page', () => {
      const wrapper = mountComponent();
      
      const cancelBtn = wrapper.find('.cancel-btn');
      expect(cancelBtn.attributes('to')).toBe('/scripts');
    });
  });

  describe('Step 4 Generation', () => {
    it('shows generation loading state on step 4', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set form data and directly set step to 4
      store.selectGenre('悬疑推理');
      store.selectDifficulty('中等');
      store.currentStep = 4;
      store.generating = true;
      store.generationStatus = '正在连接 LLM...';
      await wrapper.vm.$nextTick();
      
      // Step 4 should show generation UI elements
      expect(wrapper.text()).toContain('正在生成剧本');
      expect(wrapper.find('.spinner').exists()).toBe(true);
      expect(wrapper.text()).toContain('正在连接 LLM');
    });

    it('shows retry button when generation fails', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set form data and directly set step to 4 with error
      store.selectGenre('悬疑推理');
      store.currentStep = 4;
      store.error = 'Generation failed';
      await wrapper.vm.$nextTick();
      
      expect(wrapper.find('.retry-btn').exists()).toBe(true);
      expect(wrapper.text()).toContain('Generation failed');
    });

    it('shows script preview when generation succeeds', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set form data and directly set step to 4 with generated script
      store.selectGenre('悬疑推理');
      store.currentStep = 4;
      store.generatedScript = {
        title: 'Test Script',
        genre: '悬疑推理',
        difficulty: '中等',
        player_count: 5,
        background_story: 'This is a test background story.',
      } as any;
      await wrapper.vm.$nextTick();
      
      expect(wrapper.find('.preview-panel').exists()).toBe(true);
      expect(wrapper.text()).toContain('Test Script');
      expect(wrapper.text()).toContain('生成结果预览');
    });
  });

  describe('Step 5 - Confirm Step', () => {
    it('shows confirm button on step 5', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set up step 5 with generated script
      store.selectGenre('悬疑推理');
      store.selectDifficulty('中等');
      store.currentStep = 5;
      store.generatedScript = {
        id: 'test-123',
        title: 'Test Script',
        genre: '悬疑推理',
        difficulty: '中等',
        player_count: 5,
        background_story: 'This is a test background story for the script.',
        roles: [
          { id: '1', name: '角色 A', age: 25, occupation: '医生', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
          { id: '2', name: '角色 B', age: 30, occupation: '律师', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
        ],
      } as any;
      await wrapper.vm.$nextTick();
      
      expect(wrapper.text()).toContain('确认剧本');
      expect(wrapper.find('.confirm-btn').exists()).toBe(true);
      expect(wrapper.find('.confirm-btn').text()).toContain('确认并保存');
      expect(wrapper.find('.regen-btn').text()).toContain('重新生成');
    });

    it('shows script preview with title, meta, and description on step 5', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set up step 5 with generated script
      store.currentStep = 5;
      store.generatedScript = {
        id: 'test-123',
        title: '谋杀之谜',
        genre: '悬疑推理',
        difficulty: '困难',
        player_count: 6,
        background_story: '这是一个关于谋杀的神秘故事。在一个雨夜，富豪王老爷在他的庄园里被发现死亡...',
        roles: [
          { id: '1', name: '林默', age: 28, occupation: '记者', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
          { id: '2', name: '张华', age: 35, occupation: '商人', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
        ],
      } as any;
      await wrapper.vm.$nextTick();
      
      expect(wrapper.find('.script-card').exists()).toBe(true);
      expect(wrapper.text()).toContain('谋杀之谜');
      expect(wrapper.text()).toContain('悬疑推理');
      expect(wrapper.text()).toContain('困难');
      expect(wrapper.text()).toMatch(/6.*人/);
      expect(wrapper.text()).toContain('这是一个关于谋杀的神秘故事');
    });

    it('shows roles preview on step 5', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set up step 5 with generated script with roles
      store.currentStep = 5;
      store.generatedScript = {
        id: 'test-123',
        title: 'Test Script',
        genre: '悬疑推理',
        difficulty: '中等',
        player_count: 4,
        background_story: 'Test story.',
        roles: [
          { id: '1', name: '角色 A', age: 25, occupation: '医生', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
          { id: '2', name: '角色 B', age: 30, occupation: '律师', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
          { id: '3', name: '角色 C', age: 28, occupation: '教师', description: '', background: '', secret_task: '', alibi: '', motive: '', relationships: [] },
        ],
      } as any;
      await wrapper.vm.$nextTick();
      
      expect(wrapper.text()).toContain('角色列表');
      expect(wrapper.text()).toContain('角色 A');
      expect(wrapper.text()).toContain('角色 B');
    });

    it('redirects to scripts list after confirm', async () => {
      const router = createMockRouter();
      const pushSpy = vi.spyOn(router, 'push');
      
      const wrapper = mount(ScriptGenerateWizard, {
        global: {
          plugins: [
            createTestingPinia({
              stubActions: false,
            }),
            router,
          ],
          stubs: { 'router-link': true },
        },
      });
      
      const store = useScriptGeneratorStore();
      store.currentStep = 5;
      store.generatedScript = {
        id: 'test-123',
        title: 'Test Script',
        genre: '悬疑推理',
        difficulty: '中等',
        player_count: 4,
        background_story: 'Test story.',
        roles: [],
      } as any;
      await wrapper.vm.$nextTick();
      
      const confirmBtn = wrapper.find('.confirm-btn');
      await confirmBtn.trigger('click');
      
      expect(pushSpy).toHaveBeenCalledWith('/scripts');
    });

    it('resets wizard on regenerate', async () => {
      const wrapper = mountComponent();
      const store = useScriptGeneratorStore();
      
      // Set up step 5 with data
      store.currentStep = 5;
      store.generatedScript = { id: 'test-123', title: 'Test' } as any;
      await wrapper.vm.$nextTick();
      
      const regenBtn = wrapper.find('.regen-btn');
      await regenBtn.trigger('click');
      
      expect(store.currentStep).toBe(1);
      expect(store.generatedScript).toBeNull();
    });
  });
});
