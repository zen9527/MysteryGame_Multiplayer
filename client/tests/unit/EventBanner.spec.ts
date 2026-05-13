import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import EventBanner from '../../src/components/game/EventBanner.vue';

describe('EventBanner', () => {
  it('renders props correctly', () => {
    const wrapper = mount(EventBanner, {
      props: {
        act: 1,
        title: 'The Murder Begins',
        content: 'A body has been discovered in the library.'
      }
    });

    expect(wrapper.text()).toContain('ACT 1');
    expect(wrapper.text()).toContain('The Murder Begins');
    expect(wrapper.text()).toContain('A body has been discovered in the library.');
  });

  it('applies correct styling classes', () => {
    const wrapper = mount(EventBanner, {
      props: {
        act: 2,
        title: 'New Clue Found',
        content: 'A suspicious letter was found.'
      }
    });

    expect(wrapper.classes()).toContain('event-banner');
    expect(wrapper.find('.act-indicator').exists()).toBe(true);
    expect(wrapper.find('.event-title').exists()).toBe(true);
    expect(wrapper.find('.event-content').exists()).toBe(true);
  });

  it('displays act indicator with correct number', () => {
    const wrapper = mount(EventBanner, {
      props: {
        act: 3,
        title: 'Final Confrontation',
        content: 'The truth is revealed.'
      }
    });

    expect(wrapper.find('.act-indicator').text()).toBe('ACT 3');
  });
});
