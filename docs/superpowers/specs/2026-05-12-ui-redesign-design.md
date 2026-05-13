# UI Redesign: Modern Flat Design with Modular Architecture

Date: 2026-05-12

## Goal

Redesign the entire frontend UI to match the modular backend architecture (Script Engine + Game Engine separation), implementing a modern flat design system with midnight purple-blue color palette.

## Design Decisions

### Navigation Architecture
- **Pattern**: Collapsible sidebar (80px → 240px on hover)
- **Style**: Scheme A - Midnight Purple Blue
- **Colors**: 
  - Background: `#1a1a2e`, `#16213e`, `#0f0f23`
  - Primary accent: `#79c0ff` (blue)
  - Secondary accent: `#d2a8ff` (purple)
  - Text: `#c9d6df`, `#8b949e`, `#666`

### Module Separation

#### 1. Script Center (剧本中心)
**Layout**: Hybrid Mode (方案 C)
- Main page: Browse scripts + Detail panel (split view)
- Independent page: Script Generation (multi-step wizard)
- Inline operations: Edit, Import/Export, Delete

**Pages**:
- `/scripts` - Script browsing (main page)
- `/scripts/generate` - LLM-driven script creation wizard
- `/scripts/edit/:id` - Manual script editing (JSON editor)

#### 2. Game Hosting (游戏主持)
**Layout**: Three-column layout
- Left (260px): Analog clock + Player list + Game status
- Center (1fr): Event banner + Chat area + Input
- Right (320px): Tabbed panel (Role/Clues/Private Messages/Actions)

**Pages**:
- `/` - Room list
- `/join/:gameId` - Room join
- `/lobby/:gameId` - Waiting lobby
- `/game/:gameId` - Game page (three-column)

#### 3. LLM Settings (LLM 配置)
**Location**: Visible in both Script Center and Game Hosting modules
- Accessible via sidebar navigation
- Settings persist across modules

## Component Specifications

### Global Design System

#### Typography
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
```

#### Spacing Scale
- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 20px
- 2xl: 24px
- 3xl: 32px

#### Border Radius
- small: 4px
- medium: 6px
- large: 8px
- xlarge: 12px
- round: 50%

#### Shadows (Flat Design - Minimal)
```css
/* Only for interactive elements on hover */
box-shadow: 0 2px 8px rgba(0,0,0,0.2);
```

### Components

#### 1. Collapsible Sidebar
```vue
<template>
  <aside class="collapsible-sidebar">
    <div class="logo">🎭</div>
    <nav class="nav-items">
      <div class="nav-item active">
        <span class="icon">🏠</span>
        <span class="text">房间列表</span>
      </div>
      <div class="nav-item">
        <span class="icon">📚</span>
        <span class="text">剧本中心</span>
      </div>
      <div class="nav-item">
        <span class="icon">⚙️</span>
        <span class="text">LLM 配置</span>
      </div>
    </nav>
  </aside>
</template>

<style>
.collapsible-sidebar {
  width: 80px;
  background: #1a1a2e;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.collapsible-sidebar:hover {
  width: 240px;
}
.nav-item .text {
  opacity: 0;
  transition: opacity 0.2s;
}
.collapsible-sidebar:hover .nav-item .text {
  opacity: 1;
}
</style>
```

#### 2. Analog Clock
```vue
<template>
  <div class="clock-container">
    <div class="analog-clock">
      <div class="clock-center"></div>
      <div v-for="mark in hourMarks" :key="mark" 
           class="hour-mark" 
           :class="{ major: mark % 3 === 0 }"
           :style="{ transform: `rotate(${mark * 30}deg)` }">
      </div>
      <div class="hand hour" :style="{ transform: `rotate(${hourDeg}deg)` }"></div>
      <div class="hand minute" :style="{ transform: `rotate(${minuteDeg}deg)` }"></div>
      <div class="hand second" :style="{ transform: `rotate(${secondDeg}deg)` }"></div>
    </div>
    <div class="digital-time">{{ digitalTime }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const hourDeg = ref(0);
const minuteDeg = ref(0);
const secondDeg = ref(0);
const digitalTime = ref('');

let timer: number;

function updateClock() {
  const now = new Date();
  hourDeg.value = (now.getHours() % 12) * 30 + now.getMinutes() * 0.5;
  minuteDeg.value = now.getMinutes() * 6 + now.getSeconds() * 0.1;
  secondDeg.value = now.getSeconds() * 6;
  digitalTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', minute: '2-digit', second: '2-digit' 
  });
}

onMounted(() => {
  updateClock();
  timer = window.setInterval(updateClock, 1000);
});

onUnmounted(() => {
  clearInterval(timer);
});
</script>
```

#### 3. Game Page Three-Column Layout
```vue
<template>
  <div class="game-container">
    <!-- Left Column -->
    <aside class="left-column">
      <AnalogClock />
      <PhaseBadge :phase="gameStore.phase" :act="gameStore.act" />
      <PlayerList :players="gameStore.players" />
    </aside>

    <!-- Center Column -->
    <main class="center-column">
      <EventBanner v-if="currentEvent" :event="currentEvent" />
      <ChatArea 
        :messages="publicMessages"
        @send="handleChatSend"
        :mode="chatMode"
        @mode-change="chatMode = $event"
      />
    </main>

    <!-- Right Column -->
    <aside class="right-column">
      <Tabs v-model="activeTab" :tabs="['角色', '线索', '私聊', '行动']" />
      <RoleCard v-if="activeTab === '角色'" :role="roleCard" />
      <ClueList v-if="activeTab === '线索'" :clues="clues" />
      <PrivateMessages v-if="activeTab === '私聊'" :messages="privateMessages" />
      <ActionButtons v-if="activeTab === '行动'" @action="handleAction" />
    </aside>
  </div>
</template>

<style>
.game-container {
  display: grid;
  grid-template-columns: 260px 1fr 320px;
  height: 100vh;
  background: #0f0f23;
}
</style>
```

#### 4. Script Center Split View
```vue
<template>
  <div class="script-center">
    <div class="left-panel">
      <ScriptFilters @filter="handleFilter" />
      <ScriptList :scripts="filteredScripts" @select="selectedScript = $event" />
    </div>
    <div class="right-panel">
      <ScriptDetail v-if="selectedScript" :script="selectedScript" />
      <EmptyState v-else message="选择剧本查看详情" />
    </div>
  </div>
</template>

<style>
.script-center {
  display: grid;
  grid-template-columns: 1fr 350px;
  height: calc(100vh - 80px);
  gap: 24px;
  padding: 24px;
}
</style>
```

### Color Palette (Midnight Purple Blue)

```css
:root {
  /* Backgrounds */
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-tertiary: #0f0f23;
  
  /* Accents */
  --accent-primary: #79c0ff;    /* Blue */
  --accent-secondary: #d2a8ff;  /* Purple */
  
  /* Text */
  --text-primary: #c9d6df;
  --text-secondary: #8b949e;
  --text-muted: #666;
  
  /* Borders */
  --border-light: rgba(255,255,255,0.05);
  --border-medium: rgba(255,255,255,0.1);
  --border-accent: rgba(121,192,255,0.3);
  
  /* Interactive */
  --hover-bg: rgba(255,255,255,0.05);
  --active-bg: rgba(121,192,255,0.15);
}
```

## Implementation Phases

### Phase 1: Design System Foundation
1. Create global CSS variables (`client/src/styles/variables.css`)
2. Update `App.vue` with new base styles
3. Create reusable component library:
   - Button variants
   - Input/Textarea
   - Card components
   - Badge/Tag
   - Tabs

### Phase 2: Navigation & Layout
1. Implement collapsible sidebar component
2. Update router layout wrapper
3. Create page transition animations

### Phase 3: Game Page
1. Three-column layout container
2. Analog clock component
3. Player list component
4. Chat area with DM/player message styling
5. Tabbed right panel (Role/Clues/Private/Actions)
6. Event banner component

### Phase 4: Script Center
1. Split-view layout
2. Script list with filters
3. Script detail panel
4. Script generation wizard (multi-step)
5. Script editor (JSON)

### Phase 5: LLM Settings
1. Provider management UI
2. Connection test
3. Model selection
4. Settings persistence

## File Structure

```
client/src/
  styles/
    variables.css          # CSS custom properties
    global.css             # Global resets + base styles
    components.css         # Component base styles
  components/
    common/
      CollapsibleSidebar.vue
      Button.vue
      Input.vue
      Card.vue
      Badge.vue
      Tabs.vue
    game/
      GameContainer.vue
      AnalogClock.vue
      PlayerList.vue
      ChatArea.vue
      EventBanner.vue
      RoleCard.vue
      ClueList.vue
      ActionButtons.vue
    script/
      ScriptCenter.vue
      ScriptList.vue
      ScriptDetail.vue
      ScriptGenerator.vue
      ScriptEditor.vue
    settings/
      LLMSettings.vue
      ProviderManager.vue
  pages/
    RoomList.vue           # Updated with new design
    RoomJoin.vue
    WaitingLobby.vue
    GamePage.vue           # Three-column layout
    ScriptsPage.vue        # Script center main
    ScriptGenerate.vue     # Generation wizard
  stores/
    game.ts                # Update for new UI state
  router.ts                # Add script center routes
```

## Migration Strategy

### Step 1: Preserve Functionality
- Keep all existing API calls and WebSocket logic
- Only replace visual layer, not business logic
- Pinia store remains unchanged (add UI-specific state only)

### Step 2: Incremental Replacement
1. Update `App.vue` base styles first
2. Replace `RoomList.vue` as proof of concept
3. Build new `GamePage.vue` alongside old version
4. Test thoroughly, then remove old components

### Step 3: Cleanup
- Delete unused components (`admin/`, `game/` scaffold folders)
- Remove old styling
- Update documentation

## Testing Checklist

- [ ] Collapsible sidebar hover behavior
- [ ] Analog clock real-time update
- [ ] Three-column layout responsive (min-width check)
- [ ] Chat message deduplication
- [ ] Tab switching performance
- [ ] Script filter functionality
- [ ] LLM settings persistence
- [ ] All existing game features work (WS, SSE, API)

## Risk Mitigation

1. **Backward compatibility**: Keep Pinia store interface unchanged
2. **Rollback plan**: Git branch before major changes
3. **Testing**: Run existing test suite after each phase
4. **User feedback**: Test with actual game session before full deploy

## Success Criteria

- [ ] Visual design matches mockup (midnight purple blue, flat)
- [ ] Analog clock updates in real-time
- [ ] Three-column game page functional
- [ ] Script center split-view working
- [ ] LLM settings accessible from both modules
- [ ] All existing features preserved (chat, clues, roles, voting)
- [ ] Performance: <100ms UI response, no layout shifts
