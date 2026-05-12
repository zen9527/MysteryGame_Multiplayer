# 渐进式改进设计方案

**日期:** 2026-05-11  
**状态:** Approved  
**优先级:** High (代码质量 + 用户体验)

---

## 概述

剧本杀项目技术债务清理与用户体验优化，采用渐进式三阶段方案：
1. **核心类型统一** - 建立从后端到前端的完整类型链
2. **关键组件清理** - 移除未使用组件，实现 Store actions
3. **用户体验优化** - 提升游戏流程流畅度和视觉反馈

总周期：3 周

---

## 阶段 1：核心类型统一

### 目标
建立从 Database → API → Frontend 的完整类型安全链，消除重复验证逻辑。

### 问题现状

```
当前类型层：
- shared/ws_types.py (Pydantic) - 定义但未实际使用
- shared/schemas.ts (Zod) - 缺少 player_id 等关键字段
- client/src/types/ws.ts - 实际使用的类型，但与 shared 不一致
- server/api/*.py - 手动验证，无 schema 共享

后果：
1. API 和前端验证逻辑重复
2. 类型不一致导致运行时错误
3. 新增字段需要同步修改多处
```

### 重构方案

#### 1.1 共享 Schema 设计

```typescript
// shared/schemas/ws.ts
import { z } from "zod";

// Chat Message
export const chatMessageSchema = z.object({
  message_id: z.string(),
  content: z.string().min(1).max(2000),
  player_id: z.string(),
  role_name: z.string(),
  timestamp: z.string().datetime(),
  from_player_name: z.string()
});
export type ChatMessage = z.infer<typeof chatMessageSchema>;

// Clue
export const clueSchema = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string(),
  unlock_phase: z.enum(["act1", "act2"]),
  clue_type: z.enum(["public", "private"]),
  related_role_id: z.string().optional()
});
export type Clue = z.infer<typeof clueSchema>;

// Role Card
export const roleCardSchema = z.object({
  role_id: z.string(),
  role_name: z.string(),
  player_id: z.string(),
  layer: z.number().int().min(1).max(3),
  content: z.string(),
  secrets: z.array(z.string()).optional()
});
export type RoleCard = z.infer<typeof roleCardSchema>;

// Game State
export const gameStateSchema = z.object({
  room_id: z.string(),
  phase: z.enum(["waiting", "playing", "ended"]),
  act: z.number().int().min(1),
  players: z.array(z.object({
    player_id: z.string(),
    role_id: z.string(),
    role_name: z.string(),
    is_admin: z.boolean()
  })),
  current_event: z.any().optional(),
  clues_unlocked: z.array(z.string())
});
export type GameState = z.infer<typeof gameStateSchema>;
```

#### 1.2 API 层集成

```python
# server/api/chat.get.ts (示例)
from fastapi import APIRouter
from pydantic import BaseModel
# 方案 A：手动映射（阶段 1 实施）
# 方案 B：使用 zod-to-pydantic 库自动转换（阶段 2 优化）

# 当前采用方案 A - 手动创建 Pydantic 模型与 Zod schema 保持字段一致

class ChatMessageResponse(BaseModel):
    message_id: str
    content: str
    player_id: str
    role_name: str
    timestamp: str
    from_player_name: str

@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(room_id: str):
    messages = await game_manager.get_messages(room_id)
    # 验证每个消息
    validated = [chat_message_schema.parse_obj(m) for m in messages]
    return validated
```

#### 1.3 前端集成

```typescript
// client/src/stores/game.ts
import { chatMessageSchema, clueSchema, roleCardSchema } from "@shared/schemas/ws";

const addMessage = (raw: unknown) => {
  const result = chatMessageSchema.safeParse(raw);
  if (!result.success) {
    console.error("Invalid message:", result.error);
    throw new ValidationError(result.error);
  }
  state.messages.push(result.data);
};

const handleClueUnlock = (raw: unknown) => {
  const result = clueSchema.safeParse(raw);
  if (!result.success) return;
  state.clues.push(result.data);
};
```

### 验收标准

- [ ] `npx tsc --noEmit` 在 client/ 目录退出码 0
- [ ] 至少 3 个核心 schema 被 API 和前端共享（chat, clue, role）
- [ ] 删除 shared/ws_types.py 或标记为 deprecated
- [ ] 添加 schema 单元测试（5+ tests）

---

## 阶段 2：关键组件清理

### 目标
移除技术债务，实现核心业务逻辑，减少代码库复杂度。

### 2.1 删除未使用组件

根据 CLAUDE.md Known Technical Debt，删除以下组件：

```
删除列表:
- client/src/components/game/AccusationPanel.vue (未使用)
- client/src/components/game/EventDisplay.vue (未使用)
- client/src/components/game/PlayerList.vue (未使用)
- client/src/components/game/PublicChatPanel.vue (未使用)
- client/src/components/game/VotePanel.vue (未使用)
- client/src/components/admin/AdminConsole.vue (未使用)
- client/src/components/admin/DmLogViewer.vue (未使用)
- client/src/components/admin/ScriptPreview.vue (完全未实现)
- client/src/components/ChatPanel.vue (被 PublicChatPanel 替代，但实际用 GamePage 内联)

保留:
- GamePage.vue (已内联实现所有功能，作为主页面)
- RoleCard.vue, ClueCardPanel.vue 等实际使用的组件
```

**验证步骤:**
1. 搜索所有 import 引用
2. 运行 E2E 测试确保无破坏
3. 删除文件并提交

### 2.2 实现 Store Actions

当前 store actions 只是 console.log stubs，需要完整实现：

```typescript
// client/src/stores/game.ts - 替换 stubs

const startGame = async (roomId: string) => {
  try {
    const res = await fetch(`/api/rooms/${roomId}/start`, { method: "POST" });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.message || "Failed to start game");
    }
    
    const data = await res.json();
    state.phase = "playing";
    state.act = 1;
    state.players = data.players;
    
    // 通知 WebSocket
    ws.send(structuredClone({ type: "game_started", room_id: roomId }));
    
    return data;
  } catch (error) {
    state.error = error;
    throw error;
  }
};

const advanceAct = async (roomId: string, newAct: number) => {
  try {
    const res = await fetch(`/api/rooms/${roomId}/advance-act`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ act: newAct })
    });
    
    if (!res.ok) throw new Error("Failed to advance act");
    
    const data = await res.json();
    
    // 处理 phase_unlock
    handlePhaseUnlock(data);
    
    // 分发新角色卡和线索
    if (data.distributed_role_cards) {
      data.distributed_role_cards.forEach(receiveRoleCard);
    }
    if (data.distributed_clues) {
      data.distributed_clues.forEach(receiveClue);
    }
    
    return data;
  } catch (error) {
    state.error = error;
    throw error;
  }
};

const sendPublicChat = async (roomId: string, content: string) => {
  try {
    const res = await fetch(`/api/rooms/${roomId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content })
    });
    
    if (!res.ok) throw new Error("Failed to send message");
    
    const message = await res.json();
    addMessage(message);
    
    // 通过 WebSocket 广播
    ws.send(structuredClone({ 
      type: "chat", 
      room_id: roomId,
      content 
    }));
    
    return message;
  } catch (error) {
    state.error = error;
    throw error;
  }
};

const handlePhaseUnlock = (data: PhaseUnlockData) => {
  state.act = data.new_act;
  state.actBanner.message = `进入第 ${data.new_act} 幕`;
  state.actBanner.show = true;
  
  // 自动隐藏 banner
  setTimeout(() => {
    state.actBanner.show = false;
  }, 5000);
};

const receiveRoleCard = (card: RoleCard) => {
  // 检查是否已接收（去重）
  if (state.distributed_role_cards.has(card.role_id)) return;
  
  state.distributed_role_cards.add(card.role_id);
  state.roleCards.push(card);
  
  // WebSocket reconnect 时可能会重发，需要 deduplication
};

const receiveClue = (clue: Clue) => {
  if (state.clues.some(c => c.id === clue.id)) return;
  
  state.clues.push(clue);
};
```

### 2.3 GamePage.vue 组件化重构

当前 GamePage.vue 有 800+ 行，需要拆分为可复用组件：

```vue
<!-- client/src/components/GamePage.vue -->
<template>
  <div class="game-page">
    <!-- 顶部横幅 -->
    <ActBanner 
      :act="store.act" 
      :message="store.actBanner.message"
      :show="store.actBanner.show"
    />
    
    <!-- 当前事件 -->
    <EventDisplay 
      :event="store.currentEvent" 
      v-if="store.currentEvent"
    />
    
    <!-- 玩家列表 -->
    <PlayerList 
      :players="store.players"
      :current-player="store.currentPlayerId"
    />
    
    <!-- 标签页 -->
    <Tabs v-model="activeTab" class="game-tabs">
      <Tab name="chat" label="公共聊天">
        <PublicChatPanel 
          :messages="store.publicMessages"
          @send="handleChatSend"
          :loading="store.sendingChat"
        />
      </Tab>
      
      <Tab name="private" label="私聊 DM">
        <PrivateChatPanel 
          :messages="store.privateMessages"
          @send="handleDmChatSend"
          :rate-limit="store.dmRateLimitRemaining"
        />
      </Tab>
      
      <Tab name="clues" label="线索">
        <ClueCardPanel 
          :clues="store.clues"
          :unlocked="store.clues_unlocked"
        />
      </Tab>
      
      <Tab name="roles" label="角色卡">
        <RoleCardGrid 
          :cards="store.roleCards"
          :current-role="store.currentRoleCard"
        />
      </Tab>
    </Tabs>
    
    <!-- 投票面板（条件显示） -->
    <VotePanel 
      v-if="store.showVote"
      :target-players="store.voteTargets"
      @vote="handleVote"
      @cancel="store.showVote = false"
    />
    
    <!-- 指控弹窗（条件显示） -->
    <AccusationModal 
      v-if="store.showAccusation"
      @submit="handleAccuse"
      @cancel="store.showAccusation = false"
    />
    
    <!-- 加载状态 -->
    <LoadingOverlay 
      v-if="store.loading"
      :message="store.loadingMessage"
      :progress="store.progress"
    />
    
    <!-- 错误提示 -->
    <ErrorMessage 
      v-if="store.error"
      :message="store.error.message"
      @dismiss="store.clearError"
      :retry="store.error.retryable ? retryAction : null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useGameStore } from '@/stores/game';
import { useWebSocket } from '@/composables/useWebSocket';
import { useGameActions } from '@/composables/useGameActions';

// 组件导入
import ActBanner from './ActBanner.vue';
import EventDisplay from './EventDisplay.vue';
import PlayerList from './PlayerList.vue';
import PublicChatPanel from './PublicChatPanel.vue';
import PrivateChatPanel from './PrivateChatPanel.vue';
import ClueCardPanel from './ClueCardPanel.vue';
import RoleCardGrid from './RoleCardGrid.vue';
import VotePanel from './VotePanel.vue';
import AccusationModal from './AccusationModal.vue';
import LoadingOverlay from './LoadingOverlay.vue';
import ErrorMessage from './ErrorMessage.vue';
import Tabs from './Tabs.vue';
import Tab from './Tab.vue';

const store = useGameStore();
const { ws } = useWebSocket();
const actions = useGameActions();

const activeTab = ref('chat');

// 事件处理
const handleChatSend = async (content: string) => {
  if (!store.currentRoomId) return;
  
  try {
    store.sendingChat = true;
    await actions.sendPublicChat(store.currentRoomId, content);
  } catch (error) {
    console.error("Failed to send chat:", error);
  } finally {
    store.sendingChat = false;
  }
};

const handleDmChatSend = async (content: string) => {
  // 实现 DM 私聊发送
};

const handleVote = async (targetPlayerId: string) => {
  await actions.castVote(targetPlayerId);
  store.showVote = false;
};

const handleAccuse = async (targetPlayerId: string, reason: string) => {
  await actions.submitAccusation(targetPlayerId, reason);
  store.showAccusation = false;
};

const retryAction = () => {
  // 重试逻辑
};
</script>

<style scoped>
.game-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.game-tabs {
  flex: 1;
  overflow: hidden;
}
</style>
```

### 验收标准

- [ ] 删除 9 个未使用组件，代码库减少 ~1500 行
- [ ] Store actions 完整实现（不再 console.log）
- [ ] GamePage.vue 拆分为 <10 个子组件，每个 <200 行
- [ ] 所有组件有基本的单元测试

---

## 阶段 3：用户体验优化

### 目标
提升游戏流程流畅度和视觉反馈，减少用户等待焦虑。

### 3.1 角色卡显示动画

```vue
<!-- client/src/components/RoleCard.vue -->
<template>
  <transition name="fade-slide">
    <div class="role-card" :class="`layer-${layer}`" v-if="visible">
      <div class="role-header">
        <h3>{{ role.name }}</h3>
        <span class="layer-badge">Layer {{ layer }}</span>
      </div>
      
      <div class="role-content">
        <p v-html="maskedContent"></p>
        
        <button 
          v-if="canReveal && !isRevealed"
          @click="reveal"
          class="reveal-btn"
        >
          揭开秘密 🔓
        </button>
      </div>
      
      <div class="role-secrets" v-if="isRevealed && role.secrets">
        <h4>秘密</h4>
        <ul>
          <li v-for="secret in role.secrets" :key="secret">{{ secret }}</li>
        </ul>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  role: RoleCard;
  layer: number;
  canReveal: boolean;
}>();

const visible = ref(false);
const isRevealed = ref(false);

// 延迟显示，营造仪式感
setTimeout(() => {
  visible.value = true;
}, 100);

const maskedContent = computed(() => {
  if (isRevealed.value) return props.role.content;
  // 模糊处理未揭示内容
  return blurText(props.role.content);
});

const reveal = () => {
  isRevealed.value = true;
};

const blurText = (text: string) => {
  // 实现文字模糊效果
  return text.replace(/./g, '■');
};
</script>

<style scoped>
.role-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.fade-slide-enter-active {
  animation: fadeSlide 0.4s ease-out;
}

.fade-slide-leave-active {
  animation: fadeSlide 0.3s ease-in reverse;
}

@keyframes fadeSlide {
  from { 
    opacity: 0; 
    transform: translateY(20px) scale(0.95); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

.layer-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.reveal-btn {
  background: white;
  color: #667eea;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s;
}

.reveal-btn:hover {
  transform: scale(1.05);
}
</style>
```

### 3.2 聊天消息去重优化

```typescript
// client/src/utils/message-dedup.ts

class MessageDeduplicator {
  private seenMessages = new Map<string, number>(); // message_id -> timestamp
  private readonly COOLDOWN_MS = 15000; // 15 秒冷却

  shouldShow(message: ChatMessage): boolean {
    const key = `${message.message_id}-${message.from_player_id}`;
    const now = Date.now();
    
    // 检查是否已见过
    if (this.seenMessages.has(key)) {
      const lastSeen = this.seenMessages.get(key)!;
      
      // 15 秒内相同消息不显示
      if (now - lastSeen < this.COOLDOWN_MS) {
        return false;
      }
    }
    
    // 记录并允许显示
    this.seenMessages.set(key, now);
    
    // 清理旧记录（防止内存泄漏）
    this.cleanupOldEntries();
    
    return true;
  }

  private cleanupOldEntries() {
    const now = Date.now();
    for (const [key, timestamp] of this.seenMessages.entries()) {
      if (now - timestamp > this.COOLDOWN_MS * 2) {
        this.seenMessages.delete(key);
      }
    }
  }
}

export const messageDeduplicator = new MessageDeduplicator();
```

### 3.3 加载状态和错误提示

```vue
<!-- client/src/components/LoadingOverlay.vue -->
<template>
  <transition name="fade">
    <div class="loading-overlay" v-if="visible">
      <div class="loading-content">
        <Spinner :size="48" />
        <p class="loading-message">{{ message || "加载中..." }}</p>
        
        <ProgressCircle 
          v-if="progress !== undefined"
          :percentage="progress"
          :size="60"
        >
          {{ progress }}%
        </ProgressCircle>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  visible: boolean;
  message?: string;
  progress?: number;
}>();
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-message {
  margin-top: 16px;
  font-size: 16px;
}
</style>
```

```vue
<!-- client/src/components/ErrorMessage.vue -->
<template>
  <transition name="slide-down">
    <div class="error-message" v-if="visible">
      <div class="error-icon">⚠️</div>
      <div class="error-content">
        <p class="error-text">{{ message }}</p>
        
        <div class="error-actions">
          <button 
            v-if="retry"
            @click="retry"
            class="retry-btn"
          >
            重试
          </button>
          <button @click="$emit('dismiss')" class="dismiss-btn">
            关闭
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
  message: string;
  retry?: () => void;
}>();

defineEmits<{
  dismiss: [];
}>();
</script>

<style scoped>
.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #fee2e2;
  border: 1px solid #ef4444;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 400px;
  z-index: 9998;
}

.error-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.retry-btn {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.dismiss-btn {
  background: transparent;
  color: #7f1d1d;
  border: 1px solid #7f1d1d;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

### 3.4 DM Chat 速率限制可视化

```vue
<!-- client/src/components/DmChatRateLimit.vue -->
<template>
  <div class="dm-rate-limit" v-if="remaining > 0">
    <ProgressCircle 
      :percentage="(30 - remaining) / 30 * 100"
      :size="40"
      :color="getColor()"
    >
      {{ remaining }}s
    </ProgressCircle>
    <span class="label">冷却中</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  remaining: number; // 剩余秒数
}>();

const getColor = computed(() => {
  if (props.remaining > 20) return '#10b981'; // 绿色
  if (props.remaining > 10) return '#f59e0b'; // 黄色
  return '#ef4444'; // 红色
});
</script>

<style scoped>
.dm-rate-limit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f3f4f6;
  border-radius: 8px;
}

.label {
  font-size: 12px;
  color: #6b7280;
}
</style>
```

### 验收标准

- [ ] 角色卡展开动画流畅（<100ms 启动）
- [ ] 聊天消息去重准确率 >99%（测试验证）
- [ ] 所有异步操作有 loading 状态
- [ ] 错误提示包含重试按钮（如适用）
- [ ] 用户满意度调查（内部测试，目标 >4/5 分）

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 类型映射复杂 | 中 | 高 | 先用手动映射，逐步自动化 Zod → Pydantic 转换 |
| 组件删除破坏功能 | 低 | 高 | 每删除一个先运行 E2E 测试，保留 git 回滚能力 |
| Store 实现 bug | 中 | 中 | 分模块实现，每模块有单元测试，逐步集成 |
| 动画性能问题 | 低 | 中 | 使用 CSS transition 而非 JS animation，测试帧率 |
| WebSocket 重连数据丢失 | 中 | 高 | 利用现有的 distributed_* 缓存机制，确保重发 |

---

## 时间线

```
Week 1 (类型统一):
  Day 1-2: 分析现有类型，设计共享 schema
  Day 3-4: 实现 API 层集成  
  Day 5:   前端集成 + 测试

Week 2 (组件清理):
  Day 1:   删除未使用组件 + 验证
  Day 2-4: 实现 Store actions
  Day 5:   GamePage.vue 重构

Week 3 (UX 优化):
  Day 1-2: 角色卡动画 + 聊天去重
  Day 3-4: Loading/Error状态 + DM 速率限制
  Day 5:   整体测试 + 文档更新
```

---

## 后续工作

完成本设计后，可继续：
1. **性能优化** - 使用 `/benchmark` 测量前后对比
2. **安全审计** - 运行 `/cso` OWASP + STRIDE 检查
3. **完整测试** - 添加 E2E 测试覆盖核心流程
4. **文档完善** - 更新 API 参考和架构文档

---

## 批准记录

- **2026-05-11**: 设计批准，开始实施
