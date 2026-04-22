import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import RoomList from '../../src/components/RoomList.vue';

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
}));

vi.stubGlobal('fetch', vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve([]),
  })
));

describe('RoomList', () => {
  it('renders correctly', () => {
    const wrapper = mount(RoomList);
    expect(wrapper.find('h1').text()).toBe('剧本杀');
  });

  it('has create room button', () => {
    const wrapper = mount(RoomList);
    expect(wrapper.find('button').text()).toBe('创建房间');
  });
});
