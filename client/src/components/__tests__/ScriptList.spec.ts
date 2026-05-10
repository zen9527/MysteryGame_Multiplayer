import { mount } from '@vue/test-utils';
import ScriptList from '@/components/ScriptList.vue';
import { useGameStore } from '@/stores/game';
import { createPinia, setActivePinia } from 'pinia';

describe('ScriptList', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('displays scripts from store', async () => {
    const store = useGameStore();
    store.availableScripts = [
      { id: '1', title: 'Test Script', genre: '悬疑推理', player_count: 6 }
    ];
    
    const wrapper = mount(ScriptList);
    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('Test Script');
  });

  it('filters by genre', async () => {
    const store = useGameStore();
    store.availableScripts = [
      { id: '1', title: 'Script 1', genre: '悬疑推理' },
      { id: '2', title: 'Script 2', genre: '古风权谋' }
    ];
    
    const wrapper = mount(ScriptList);
    await wrapper.vm.$nextTick();
    
    const genreFilter = wrapper.find('[data-testid="genre-filter"]');
    await genreFilter.setValue('悬疑推理');
    
    expect(wrapper.text()).toContain('Script 1');
    expect(wrapper.text()).not.toContain('Script 2');
  });

  it('emits select event on card click', async () => {
    const store = useGameStore();
    store.availableScripts = [
      { id: '1', title: 'Test Script' }
    ];
    
    const wrapper = mount(ScriptList);
    await wrapper.vm.$nextTick();
    
    const card = wrapper.find('.script-card');
    await card.trigger('click');
    
    expect(wrapper.emitted('select')).toBeTruthy();
    expect(wrapper.emitted('select')?.[0]).toEqual(['1']);
  });

  it('shows empty state when no scripts', async () => {
    const store = useGameStore();
    store.availableScripts = [];
    
    const wrapper = mount(ScriptList);
    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('暂无剧本');
  });
});
