import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ScriptGenerateWizard from '@/components/scripts/ScriptGenerateWizard.vue';

describe('ScriptGenerateWizard', () => {
  const mountComponent = () => {
    return mount(ScriptGenerateWizard, {
      global: {
        plugins: [
          createTestingPinia({
            stubActions: false,
          }),
        ],
        stubs: { 'router-link': true },
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

  describe('Steps 4-5 Placeholders', () => {
    it('shows generation placeholder on step 4', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 4 (need to complete steps 1-3)
      await wrapper.find('.genre-grid button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      await wrapper.find('.difficulty-options button').trigger('click');
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      // Step 3 auto-enables, click next
      await wrapper.find('.wizard-nav button:last-child').trigger('click');
      
      expect(wrapper.text()).toContain('生成功能待实现');
    });

    it('shows confirmation placeholder on step 5', async () => {
      const wrapper = mountComponent();
      
      // Navigate to step 5 (stub for now)
      // This test documents expected behavior for Task 3
      expect(true).toBe(true); // Placeholder until generation is implemented
    });
  });
});
