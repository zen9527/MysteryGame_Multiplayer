import { mount } from '@vue/test-utils';
import ScriptDetail from '@/components/ScriptDetail.vue';
import { scriptApi } from '@/types/script';

vi.mock('@/types/script', () => ({
  scriptApi: {
    getDetail: vi.fn()
  }
}));

describe('ScriptDetail', () => {
  it('loads and displays script detail', async () => {
    vi.mocked(scriptApi.getDetail).mockResolvedValue({
      id: '1',
      title: 'Test Script',
      genre: '悬疑推理',
      difficulty: '中等',
      player_count: 6,
      estimated_time: 120,
      background_story: 'Test story',
      roles: [{ id: '1', name: '角色 A', age: 30, occupation: '医生', description: '描述', background: '背景', secret_task: '任务', alibi: '不在场证明' }],
      plot_outline: { act1: '第一幕', act2: '第二幕', act3: '第三幕' }
    });

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('Test Script');
    expect(wrapper.text()).toContain('角色 A');
  });

  it('hides sensitive fields', async () => {
    vi.mocked(scriptApi.getDetail).mockResolvedValue({
      id: '1',
      title: 'Test Script',
      roles: [],
      plot_outline: { act1: '第一幕', act2: '第二幕', act3: '第三幕' }
    });

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).not.toContain('true_killer');
    expect(wrapper.text()).not.toContain('murder_method');
    expect(wrapper.text()).not.toContain('clues');
  });

  it('shows loading state', async () => {
    vi.mocked(scriptApi.getDetail).mockImplementation(() => new Promise(() => {}));

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    expect(wrapper.text()).toContain('加载中...');
  });

  it('shows error when load fails', async () => {
    vi.mocked(scriptApi.getDetail).mockRejectedValue(new Error('Failed'));

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('加载剧本失败');
  });

  it('emits back and start events', async () => {
    vi.mocked(scriptApi.getDetail).mockResolvedValue({
      id: '1',
      title: 'Test Script',
      roles: [],
      plot_outline: { act1: '', act2: '', act3: '' }
    });

    const wrapper = mount(ScriptDetail, {
      props: { scriptId: '1' }
    });

    await wrapper.vm.$nextTick();

    const backBtn = wrapper.find('.back-btn');
    await backBtn.trigger('click');
    expect(wrapper.emitted('back')).toBeTruthy();

    const startBtn = wrapper.find('.start-btn');
    await startBtn.trigger('click');
    expect(wrapper.emitted('start')).toBeTruthy();
  });
});
