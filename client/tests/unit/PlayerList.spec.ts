import { describe, it, expect, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import PlayerList from '../../src/components/game/PlayerList.vue';

interface TestPlayer {
  id: string;
  name: string;
  roleName: string;
  roleTitle: string;
  layer: number;
  onlineTime: number;
  lastActivity: number;
}

describe('PlayerList', () => {
  const createPlayers = (override?: Partial<TestPlayer>): TestPlayer[] => [
    {
      id: '1',
      name: '张三',
      roleName: '林默',
      roleTitle: '侦探',
      layer: 2,
      onlineTime: 3600,
      lastActivity: Date.now(),
      ...override
    }
  ];

  it('renders player list correctly', () => {
    const players = createPlayers();
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    expect(wrapper.find('.player-list').exists()).toBe(true);
    expect(wrapper.findAll('.player-card').length).toBe(1);
  });

  it('displays multiple players', () => {
    const players = [
      ...createPlayers(),
      ...createPlayers({ id: '2', name: '李四', roleName: '王五', roleTitle: '嫌疑人' })
    ];
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    expect(wrapper.findAll('.player-card').length).toBe(2);
  });

  it('player card displays name, role, layer, online time', () => {
    const players = createPlayers();
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    const card = wrapper.find('.player-card');
    
    expect(card.find('.player-name').text()).toBe('张三');
    expect(card.find('.player-role').text()).toContain('林默');
    expect(card.find('.player-role').text()).toContain('侦探');
    expect(card.find('.player-info').text()).toContain('Layer 2');
    expect(card.find('.player-info').text()).toContain('1h 0m');
  });

  it('idle status indicator shows when player inactive >60s', () => {
    const players = createPlayers({
      lastActivity: Date.now() - 120000 // 2 minutes ago
    });
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    const statusIndicator = wrapper.find('.player-status');
    expect(statusIndicator.classes()).toContain('idle');
  });

  it('active player does not show idle status', () => {
    const players = createPlayers({
      lastActivity: Date.now() // active now
    });
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    const statusIndicator = wrapper.find('.player-status');
    expect(statusIndicator.classes()).not.toContain('idle');
  });

  it('formats time correctly for seconds < 60', () => {
    const players = createPlayers({ onlineTime: 45 });
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    expect(wrapper.find('.player-info').text()).toContain('45s');
  });

  it('formats time correctly for minutes', () => {
    const players = createPlayers({ onlineTime: 125 }); // 2 minutes 5 seconds
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    expect(wrapper.find('.player-info').text()).toContain('2m');
  });

  it('formats time correctly for hours', () => {
    const players = createPlayers({ onlineTime: 3665 }); // 1 hour 1 minute 5 seconds
    const wrapper = mount(PlayerList, {
      props: { players }
    });

    expect(wrapper.find('.player-info').text()).toContain('1h');
  });
});
