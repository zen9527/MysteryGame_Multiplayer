# 剧本杀 — 信息隔离与角色卡重构设计

## 问题

当前所有 DM 生成的对话、事件、角色信息全部广播给所有玩家，导致：
- 凶手/侦探身份公开，游戏无法进行
- DM 私信暴露给所有人
- 玩家无法查看自己的角色卡、秘密任务、个人线索
- 线索无区分，个人线索和公共线索混在一起

## 设计决策

| # | 问题 | 选择 |
|---|------|------|
| 1 | 信息分发模式 | **C** — 阶段自动解锁 + 角色卡随时翻阅 |
| 2 | 角色卡分层 | **C** — 3 层逐步解锁 |
| 3 | 后端消息路由 | **A** — 扩展现有 WebSocketHub |
| 4 | 阶段数量 | **C** — 灵活幕数 + 实时进度显示 |
| 5 | DM 私信触发 | **A+C** — DM 随时推送 + 玩家主动请求 |
| 6 | 剧本生成扩展 | **B** — 线索分发 + private_events |
| 7 | 线索展示 | **B** — 线索卡片 |

## 架构

### 界面布局

```
┌─────────────────────────────────────────────────────────────┐
│  Header: 剧本名 | 阶段 | 幕数 | 计时器                        │
├─────────────────────────────────────────────────────────────┤
│  左侧：公共信息区（所有人可见）              │ 右侧：私人信息区 │
│                                          │  （仅自己可见）    │
│  ┌──────────────────────────────┐        │  Tab 导航：        │
│  │ 📜 公共事件                   │        │  [角色卡] [私信]   │
│  │ DM 推送的公共事件              │        │  [线索] [操作]    │
│  └──────────────────────────────┘        │                    │
│  ┌──────────────────────────────┐        │  ┌──────────────┐  │
│  │ 💬 公共聊天                   │        │  │ 角色卡内容   │  │
│  │ 玩家公共消息                   │        │  │ （Tab 1）    │  │
│  │                              │        │  └──────────────┘  │
│  │ [输入框] [发送]                │        │  ┌──────────────┐  │
│  └──────────────────────────────┘        │  │ 私信内容     │  │
│                                          │  │ （Tab 2）    │  │
│                                          │  └──────────────┘  │
│                                          │  ┌──────────────┐  │
│                                          │  │ 线索卡片     │  │
│                                          │  │ （Tab 3）    │  │
│                                          │  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 信息隔离规则

| 信息类型 | 可见范围 | 分发方式 |
|----------|----------|----------|
| 公共事件 | 所有玩家 | `broadcast()` |
| 公共聊天 | 所有玩家 | `broadcast()` |
| 角色卡 | 仅本人 | `send_to_player()` |
| 玩家列表 | 玩家名字可见，角色名/身份隐藏 | `broadcast()`（只显示 name，不显示 role） |
| DM→玩家私信 | 仅 DM 和该玩家 | `send_to_player()` |
| 玩家间私聊 | 仅两个玩家 | `send_to_player()` × 2 |
| 个人线索 | 仅分配的玩家 | `send_to_player()` |
| 公共线索 | 所有玩家 | `broadcast()` |
| 投票结果 | 所有玩家 | `broadcast()` |
| 真相揭晓 | 所有玩家 | `broadcast()` |
| 投票面板 | 只显示玩家名字，不显示角色名 | 前端限制 |

### 角色卡分层

| 层级 | 内容 | 解锁阶段 |
|------|------|----------|
| 第 1 层 | 角色名、一句话简介 | 剧本生成后（lobby 阶段） |
| 第 2 层 | 背景故事、秘密任务、不在场证明 | 第 1 幕开始时 |
| 第 3 层 | 人际关系、动机、个人专属线索 | 第 2 幕开始时 |

### 阶段自动解锁

| 阶段 | 自动推送内容 |
|------|-------------|
| Lobby（剧本生成后） | 角色卡第 1 层（角色名 + 简介） |
| 第 1 幕（背景介绍） | 角色卡第 2 层（背景/秘密任务/不在场证明） + 剧情大纲 act1 |
| 第 2 幕（自由调查） | 角色卡第 3 层（人际关系/动机/个人线索） + 剧情大纲 act2 + DM 私信触发点 |
| 第 3 幕（总结陈词） | 剧情大纲 act3（如有） |
| 审判阶段 | 投票入口 + 指控面板 |
| 真相揭晓 | 全部信息公开 |

## 后端改动

### 1. `server/models.py` — 扩展剧本模型

```python
class Clue(BaseModel):
    id: str
    title: str
    content: str
    target_role: Optional[str] = None
    is_red_herring: bool = False
    content_hint: str
    # 新增
    target_player_ids: List[str] = Field(default_factory=list)  # 分配给哪些玩家
    unlock_phase: str = "act2"  # 解锁阶段
    trigger_condition: Optional[str] = None  # 触发条件

class PrivateEvent(BaseModel):
    """DM 私信触发点"""
    phase: str  # 对应阶段
    target_player_id: str  # 目标玩家
    content: str  # DM 私信内容
    trigger: Optional[str] = None  # 触发条件（如"玩家请求线索时"）
```

### 2. `server/game_manager.py` — 新增分发方法

```python
def distribute_role_card(self, game_id: str, player_id: str, layer: str):
    """分发角色卡指定层级给玩家"""

def distribute_clue(self, game_id: str, clue: Clue, player_id: str):
    """分发线索给特定玩家"""

def execute_private_events(self, game_id: str, phase: str):
    """执行当前阶段的所有 DM 私信触发点"""

def unlock_phase(self, game_id: str, new_phase: str):
    """阶段解锁：自动分发该阶段的所有信息"""
```

### 3. `server/websocket_hub.py` — 正确使用分发方法

```python
# 当前所有消息都用 broadcast()，需要按类型区分：
if msg_type == "chat":
    broadcast()  # 公共聊天 — 保持广播
elif msg_type == "private_chat":
    send_to_player(sender) + send_to_player(target)  # 已有，保持
elif msg_type == "clue_reveal":
    if clue.public:
        broadcast()
    else:
        send_to_player(clue.target_player_id)
elif msg_type == "dm_private":
    send_to_player(target_player_id)  # 新增
```

### 4. `server/host_dm.py` — 剧本生成扩展

LLM prompt 增加指令：
- 为每条线索标注 `target_player_ids` 和 `unlock_phase`
- 生成 `private_events` 数组（DM 私信触发点）
- 标注角色卡每层解锁时机

## 前端改动

### 1. `client/src/components/GamePage.vue` — 重构布局

- 左侧：公共事件 + 公共聊天（保持现有结构，微调样式）
- 右侧：Tab 导航（角色卡 / 私信 / 线索 / 操作）
- 新增 `RoleCard.vue` 组件
- 新增 `PrivateChatPanel.vue` 组件
- 新增 `ClueCardPanel.vue` 组件

### 2. `client/src/types/ws.ts` — 新增消息类型

```typescript
export type WSMessage =
  // 现有类型...
  | { type: "role_card"; layer: "1" | "2" | "3"; data: Role }
  | { type: "dm_private"; from: "__dm__"; to: string; content: string }
  | { type: "clue_unlock"; clue: ClueData }
  | { type: "phase_unlock"; phase: string; events: string[] }
  | { type: "private_event_trigger"; event: PrivateEventData }
```

### 3. `client/src/stores/game.ts` — 新增状态

```typescript
const roleCard = ref<{ layer1: Role; layer2: Role; layer3: Role }>({
  layer1: null, layer2: null, layer3: null
});
const privateMessages = ref<Array<{ from: string; content: string }>>([]);
const clues = ref<Array<ClueData>>([]);
const activeTab = ref<'role' | 'private' | 'clue' | 'action'>('role');
```

## 进度显示

- **剧本生成阶段**：SSE 流显示百分比 + 当前步骤（"正在生成角色..."、"正在设计线索..."、"正在规划私信..."）
- **DM 生成事件**：WebSocket 推送 `generating` 状态 → 前端显示加载动画 → 完成后推送事件内容

## 管理员面板扩展

- 新增"私信面板"：选择目标玩家 + 输入内容 → 发送私信
- 新增"手动解锁"：强制解锁特定阶段信息给特定玩家
- 保持现有功能：推送事件、强制审判、结束游戏、追加线索
