import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import ChatArea from '../../src/components/game/ChatArea.vue';

describe('ChatArea', () => {
  const mockMessages = [
    {
      id: '1',
      from: '玩家 A',
      content: '我觉得凶手是 B',
      timestamp: '10:30'
    },
    {
      id: '2',
      from: 'DM',
      content: '请提供更多证据',
      timestamp: '10:31'
    }
  ];

  it('renders chat messages correctly', () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: mockMessages
      }
    });

    expect(wrapper.findAll('.message').length).toBe(2);
    expect(wrapper.find('.message-from').text()).toBe('玩家 A');
    expect(wrapper.find('.message-content').text()).toBe('我觉得凶手是 B');
  });

  it('styles DM messages differently from player messages', () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: mockMessages
      }
    });

    const dmMessage = wrapper.findAll('.message').at(1);
    expect(dmMessage?.classes()).toContain('dm');
    
    const playerMessage = wrapper.findAll('.message').at(0);
    expect(playerMessage?.classes()).not.toContain('dm');
  });

  it('displays message header with from and timestamp', () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: mockMessages
      }
    });

    const firstMessage = wrapper.findAll('.message').at(0);
    expect(firstMessage?.find('.message-from').text()).toBe('玩家 A');
    expect(firstMessage?.find('.message-time').text()).toBe('10:30');
  });

  it('defaults to public mode', () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const publicBtn = wrapper.findAll('.mode-btn').at(0);
    expect(publicBtn?.classes()).toContain('active');
  });

  it('emits mode update when clicking mode buttons', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const privateBtn = wrapper.findAll('.mode-btn').at(1);
    await privateBtn?.trigger('click');

    expect(wrapper.emitted('update:mode')).toBeTruthy();
    expect(wrapper.emitted('update:mode')?.[0]).toEqual(['private']);
  });

  it('emits send event when clicking send button', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const input = wrapper.find('.chat-input');
    await input.setValue('测试消息');

    const sendBtn = wrapper.find('.send-btn');
    await sendBtn.trigger('click');

    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('send')?.[0]).toEqual(['测试消息', 'public']);
  });

  it('does not send empty messages', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const input = wrapper.find('.chat-input');
    await input.setValue('   ');

    const sendBtn = wrapper.find('.send-btn');
    await sendBtn.trigger('click');

    expect(wrapper.emitted('send')).toBeFalsy();
  });

  it('handles Enter key to send message', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const input = wrapper.find('.chat-input');
    await input.setValue('测试消息');
    await input.trigger('keyup.enter');

    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('send')?.[0]).toEqual(['测试消息', 'public']);
  });

  it('allows newline with Shift+Enter', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const input = wrapper.find('.chat-input');
    await input.setValue('测试消息');
    await input.trigger('keyup.enter', { shiftKey: true });

    expect(wrapper.emitted('send')).toBeFalsy();
    expect(input.element.value).toBe('测试消息');
  });

  it('clears input after sending', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: []
      }
    });

    const input = wrapper.find('.chat-input');
    await input.setValue('测试消息');

    const sendBtn = wrapper.find('.send-btn');
    await sendBtn.trigger('click');

    expect(input.element.value).toBe('');
  });

  it('shows correct placeholder based on mode', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: [],
        mode: 'private'
      }
    });

    const input = wrapper.find('.chat-input');
    expect(input.attributes('placeholder')).toBe('向 DM 提问...');

    await wrapper.setProps({ mode: 'public' });
    expect(input.attributes('placeholder')).toBe('输入你的推理或问题...');
  });

  it('emits send event with correct mode', async () => {
    const wrapper = mount(ChatArea, {
      props: {
        messages: [],
        mode: 'private'
      }
    });

    const input = wrapper.find('.chat-input');
    await input.setValue('私密问题');

    const sendBtn = wrapper.find('.send-btn');
    await sendBtn.trigger('click');

    expect(wrapper.emitted('send')?.[0]).toEqual(['私密问题', 'private']);
  });
});
