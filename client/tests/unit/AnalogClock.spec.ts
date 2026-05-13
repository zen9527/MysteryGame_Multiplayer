import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import AnalogClock from '../../src/components/game/AnalogClock.vue';

describe('AnalogClock', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders with correct structure', () => {
    const wrapper = mount(AnalogClock);
    
    expect(wrapper.find('.clock-container').exists()).toBe(true);
    expect(wrapper.find('.analog-clock').exists()).toBe(true);
    expect(wrapper.find('.clock-center').exists()).toBe(true);
    expect(wrapper.find('.digital-time').exists()).toBe(true);
    expect(wrapper.find('.clock-label').exists()).toBe(true);
    
    // Should have 12 hour marks
    expect(wrapper.findAll('.hour-mark').length).toBe(12);
    
    // Should have 3 hands
    expect(wrapper.find('.hand.hour').exists()).toBe(true);
    expect(wrapper.find('.hand.minute').exists()).toBe(true);
    expect(wrapper.find('.hand.second').exists()).toBe(true);
  });

  it('displays digital time in correct format', async () => {
    vi.setSystemTime(new Date('2024-01-15T14:30:45'));
    
    const wrapper = mount(AnalogClock);
    
    // Advance timers to trigger onMounted callback
    await vi.advanceTimersByTimeAsync(0);
    await wrapper.vm.$nextTick();
    
    expect(wrapper.find('.digital-time').text()).toBe('14:30:45');
  });

  it('rotates hour hand correctly', async () => {
    vi.setSystemTime(new Date('2024-01-15T03:00:00'));
    
    const wrapper = mount(AnalogClock);
    await vi.advanceTimersByTimeAsync(0);
    await wrapper.vm.$nextTick();
    
    // At 3:00, hour hand should be at 90 degrees (3 * 30)
    const hourHand = wrapper.find('.hand.hour');
    expect(hourHand.attributes('style')).toContain('rotate(90deg)');
  });

  it('rotates minute hand correctly', async () => {
    vi.setSystemTime(new Date('2024-01-15T10:30:00'));
    
    const wrapper = mount(AnalogClock);
    await vi.advanceTimersByTimeAsync(0);
    await wrapper.vm.$nextTick();
    
    // At 30 minutes, minute hand should be at 180 degrees (30 * 6)
    const minuteHand = wrapper.find('.hand.minute');
    expect(minuteHand.attributes('style')).toContain('rotate(180deg)');
  });

  it('rotates second hand correctly', async () => {
    vi.setSystemTime(new Date('2024-01-15T10:30:45'));
    
    const wrapper = mount(AnalogClock);
    await vi.advanceTimersByTimeAsync(0);
    await wrapper.vm.$nextTick();
    
    // At 45 seconds, second hand should be at 270 degrees (45 * 6)
    const secondHand = wrapper.find('.hand.second');
    expect(secondHand.attributes('style')).toContain('rotate(270deg)');
  });

  it('updates clock every second', async () => {
    vi.setSystemTime(new Date('2024-01-15T10:30:00'));
    
    const wrapper = mount(AnalogClock);
    await vi.advanceTimersByTimeAsync(0);
    await wrapper.vm.$nextTick();
    
    expect(wrapper.find('.digital-time').text()).toBe('10:30:00');
    
    // Advance 1 second
    await vi.advanceTimersByTimeAsync(1000);
    await wrapper.vm.$nextTick();
    
    expect(wrapper.find('.digital-time').text()).toBe('10:30:01');
  });

  it('cleans up timer on unmount', () => {
    const wrapper = mount(AnalogClock);
    
    const clearIntervalSpy = vi.spyOn(window, 'clearInterval');
    
    wrapper.unmount();
    
    expect(clearIntervalSpy).toHaveBeenCalled();
  });

  it('marks every 3rd hour mark as major', () => {
    const wrapper = mount(AnalogClock);
    
    const majorMarks = wrapper.findAll('.hour-mark.major');
    expect(majorMarks.length).toBe(4); // 3, 6, 9, 12
  });
});
