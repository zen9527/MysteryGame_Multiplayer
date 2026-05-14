import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ErrorBoundary from '@/components/common/ErrorBoundary.vue';

describe('ErrorBoundary', () => {
  it('should show error when error is set', async () => {
    const wrapper = mount(ErrorBoundary);
    
    // Set error
    wrapper.vm.setError(new Error('Test error'));
    await wrapper.vm.$nextTick();
    
    expect(wrapper.find('.error-boundary').exists()).toBe(true);
    expect(wrapper.text()).toContain('Test error');
  });

  it('should show slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: { default: '<div>Content</div>' }
    });
    
    expect(wrapper.find('.error-boundary').exists()).toBe(false);
    expect(wrapper.text()).toContain('Content');
  });

  it('should call onRetry when retry button clicked', async () => {
    const onRetry = vi.fn().mockResolvedValue(undefined);
    const wrapper = mount(ErrorBoundary, {
      props: { onRetry },
      slots: { default: '<div>Content</div>' }
    });
    
    // Set error
    wrapper.vm.setError(new Error('Test'));
    await wrapper.vm.$nextTick();
    
    // Click retry - find button by text content
    const retryButton = wrapper.findAll('button').find(btn => btn.text().includes('Retry'));
    expect(retryButton).toBeDefined();
    await retryButton!.trigger('click');
    
    expect(onRetry).toHaveBeenCalled();
  });

  it('should emit dismiss event when dismiss button clicked', async () => {
    const wrapper = mount(ErrorBoundary);
    
    // Set error first so buttons are rendered
    wrapper.vm.setError(new Error('Test error'));
    await wrapper.vm.$nextTick();
    
    // Find dismiss button by text content
    const dismissButton = wrapper.findAll('button').find(btn => btn.text().includes('Dismiss'));
    expect(dismissButton).toBeDefined();
    await dismissButton!.trigger('click');
    
    expect(wrapper.emitted('dismiss')).toBeTruthy();
  });
});
