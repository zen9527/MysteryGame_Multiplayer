import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';

describe('LoadingSpinner', () => {
  it('should render spinner without message', () => {
    const wrapper = mount(LoadingSpinner);
    expect(wrapper.find('.spinner').exists()).toBe(true);
    expect(wrapper.find('p').exists()).toBe(false);
  });

  it('should render spinner with message', () => {
    const wrapper = mount(LoadingSpinner, {
      props: { message: '加载中...' }
    });
    expect(wrapper.find('.spinner').exists()).toBe(true);
    expect(wrapper.text()).toContain('加载中...');
  });

  it('should have inline class when inline prop is set', () => {
    const wrapper = mount(LoadingSpinner, {
      props: { inline: true }
    });
    expect(wrapper.classes()).toContain('inline');
  });
});
