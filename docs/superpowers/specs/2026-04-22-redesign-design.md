# 剧本杀 — 重新设计方案

> 日期: 2026-04-22
> 状态: 已确认，待实施

## 1. 项目概述

重新设计本地剧本杀应用，从 PyQt6 桌面应用改为 **浏览器客户端 + FastAPI 服务器** 架构。核心改进：

- **自由探索游戏流程** — 取消固定阶段，LLM 主持人动态推进剧情
- **LLM 全权 DM** — LLM 全程主持游戏，不只是生成剧本
- **局域网多人在线** — 浏览器客户端通过 WebSocket 连接同一服务器

## 2. 技术栈

| 层 | 技术 | 理由 |
|---|---|---|
| 后端 | Python 3.14 + FastAPI | 与现有 LLM 集成无缝，异步原生支持 |
| 通信 | WebSocket (FastAPI WebSocket) | 双向实时通信，服务器主动推送事件 |
| 前端 | Vue 3 Composition API + Vite + TypeScript | SPA 交互灵活，角色卡/线索/投票等 UI 丰富 |
| LLM | OpenAI 兼容 API (LM Studio / Ollama) | 沿用现有配置，不改动 |
| 数据存储 | 内存 (游戏进行中) + JSON (存档) | 剧本杀是会话型应用，不需要持久化数据库 |

## 3. 架构

```
                    ┌──────────────────────────────┐
                    │        FastAPI 服务器         │
                    │                              │
                    │  ┌────────────────────────┐  │
                    │  │ WebSocket Hub          │  │
                    │  │ - 房间创建/加入/离开    │  │
                    │  │ - 消息广播/私发         │  │
                    │  │ - 房间状态管理          │  │
                    │  └───────────┬────────────┘  │
                    │              │               │
                    │  ┌───────────▼────────────┐  │
                    │  │ GameManager            │  │
                    │  │ - 游戏状态机            │  │
                    │  │ - 玩家管理              │  │
                    │  │ - 线索/指控/投票管理    │  │
                    │  └───────────┬────────────┘  │
                    │              │               │
                    │  ┌───────────▼────────────┐  │
                    │  │ LLM Host DM            │  │
                    │  │ - 剧本生成              │  │
                    │  │ - 事件发布              │  │
                    │  │ - 线索投放决策          │  │
                    │  │ - 游戏节奏控制          │  │
                    │  │ - 真相复盘              │  │
                    │  └────────────────────────┘  │
                    └──────┬──────┬──────┬─────────┘
                           │      │      │
                      WS   │      │      │ WS
                     ┌─────▼┐ ┌──▼────┐ ┌▼────────┐
                     │浏览器│ │浏览器 │ │浏览器   │
                     │客户端│ │客户端 │ │客户端   │
                     │(玩家A)│ │(玩家B)│ │(玩家C)  │
                     └──────┘ └───────┘ └─────────┘
```

### 3.1 职责边界

| 模块 | 职责 | 不做什么 |
|---|---|---|
| WebSocket Hub | 房间 CRUD、消息路由、连接管理 | 不做游戏逻辑 |
| GameManager | 游戏状态、玩家管理、线索/投票/指控 | 不做 LLM 调用 |
| LLM Host DM | 剧情生成、事件发布、线索投放、复盘 | 不直接操作 WebSocket |
| 浏览器客户端 | UI 渲染、玩家输入、WebSocket 收发 | 不做游戏逻辑 |

## 4. 游戏流程

### 4.1 生命周期

```
创建房间 → 玩家加入 → 角色分配 → 游戏开始
  ↓
[事件轮次循环]
  LLM 发布事件 → 玩家自由行动 → LLM 根据反馈决定下一步
  ↓
[审判环节]（当有指控时触发）
  公开辩论 → 投票 → 多数达成
  ↓
[真相揭晓]
  LLM 复盘整个故事，评价玩家表现
  ↓
游戏结束
```

### 4.2 事件轮次

服务器每轮做 3 件事：
1. **发布事件** — "你在角落里发现了一张纸条"
2. **推送线索** — 可能全公开，也可能只给特定玩家
3. **等待玩家行动**

玩家每轮可以做：
- 公共频道发言（讨论线索、推理）
- 向特定玩家发起私聊
- 投出「指控」（指定嫌疑人 + 理由）
- 请求 LLM 主持人推进/放出线索

### 4.3 游戏结束判定

| 条件 | 触发方式 | 结果 |
|---|---|---|
| 投票达成共识 | ≥2 人指控同一人 → 全体投票 ≥50% | 真相揭晓，正常结束 |
| 正确指控 | 投票结果 = 真凶 | 胜利动画 + 复盘，完美结束 |
| 超时/线索耗尽 | 60 分钟或所有线索已公开 | 最后投票机会 → 真相揭晓 |

**关键规则：LLM DM 不能单方面终结游戏。** 所有正常结束必须经过玩家投票。

## 5. 数据模型

### 5.1 核心模型

```python
# 剧本
class Script:
    title: str
    genre: str                         # 悬疑推理/古风权谋/现代都市/恐怖惊悚/欢乐搞笑/科幻未来
    difficulty: str                    # 简单/中等/困难
    estimated_time: int                # 分钟
    background_story: str              # 世界观背景
    true_killer: str                   # 真凶角色名
    murder_method: str                 # 作案手法
    cover_up: str                      # 掩盖手段
    roles: list[Role]
    clues: list[Clue]                  # 预设线索池
    plot_outline: PlotOutline

# 角色
class Role:
    id: str
    name: str
    age: int
    occupation: str
    description: str                   # 公开描述
    background: str                    # 角色背景故事
    secret_task: str                   # 秘密任务（仅该玩家可见）
    alibi: str                         # 不在场证明
    motive: str                        # 作案动机
    relationships: list[Relationship]

# 线索
class Clue:
    id: str
    title: str
    content: str
    target_role: str | None            # 只对特定角色揭示
    is_red_herring: bool               # 是否为误导线索
    content_hint: str                  # 线索摘要（给主持人的提示）

# 玩家
class Player:
    id: str                            # WebSocket session id
    name: str                          # 玩家显示名
    role_id: str                       # 分配的角色
    role: Role                         # 完整角色数据（仅发给该玩家）
    status: str                        # connected/playing/left
    has_read_role: bool                # 是否已阅读角色卡

# 消息
class Message:
    id: str
    from_player_id: str
    content: str
    timestamp: datetime
    type: str                          # public/private/system/event
    to_player_id: str | None           # 私聊目标

# 指控
class Accusation:
    id: str
    from_player_id: str
    target_role_name: str
    reasoning: str
    timestamp: datetime

# 投票
class Vote:
    id: str
    from_player_id: str
    target_role_name: str
    reasoning: str
    timestamp: datetime

# 游戏状态
class GameState:
    game_id: str
    phase: str                         # waiting/playing/trial/revealed/finished
    players: dict[str, Player]         # player_id -> Player
    script: Script
    public_messages: list[Message]
    private_messages: list[Message]
    accusations: list[Accusation]
    votes: list[Vote]
    timer_start: datetime
    max_duration_minutes: int = 60
    current_round: int
    host_message_history: list[str]    # LLM DM 的历史消息（用于上下文）
```

## 6. API 设计

### 6.1 REST API

| 方法 | 路径 | 描述 |
|---|---|---|
| POST | `/api/rooms` | 创建房间 |
| GET | `/api/rooms` | 列出所有房间 |
| GET | `/api/rooms/{id}` | 获取房间信息（不含敏感数据） |
| DELETE | `/api/rooms/{id}` | 销毁房间 |
| GET | `/api/health` | 健康检查 |

### 6.2 WebSocket 协议

**连接:** `ws://host:port/ws/{room_id}`

#### 客户端 → 服务器消息

```jsonc
// 加入游戏
{ "type": "join", "player_name": "张三" }

// 确认已阅读角色卡
{ "type": "role_read", "player_id": "xxx" }

// 公共发言
{ "type": "chat", "content": "我觉得凶手是李四" }

// 私聊
{ "type": "private_chat", "to_player_id": "yyy", "content": "我有线索要告诉你" }

// 指控
{ "type": "accuse", "target_role_name": "李四", "reasoning": "因为..." }

// 投票
{ "type": "vote", "target_role_name": "李四", "reasoning": "证据是..." }

// 请求推进
{ "type": "request_advance" }
```

#### 服务器 → 客户端消息

```jsonc
// 系统通知
{ "type": "system", "content": "所有玩家已就位，游戏开始！" }

// LLM 事件发布
{ "type": "event", "content": "你在书房发现了一封未寄出的信..." }

// 线索揭示（公开）
{ "type": "clue_reveal", "clue": { ... }, "public": true }

// 线索揭示（仅该玩家）
{ "type": "clue_reveal", "clue": { ... }, "public": false, "to_player_id": "xxx" }

// 公共聊天
{ "type": "chat", "from": "张三", "content": "...", "timestamp": "..." }

// 私聊
{ "type": "private_chat", "from": "张三", "content": "...", "timestamp": "..." }

// 指控公告
{ "type": "accusation", "from": "张三", "target": "李四", "reasoning": "..." }

// 审判开始
{ "type": "trial_start", "accusations": [...] }

// 投票结果
{ "type": "vote_result", "round": 1, "results": { "李四": 3, "王五": 1 }, "consensus": false }

// 真相揭晓
{ "type": "reveal", "truth": { ... }, "player_evaluations": { ... } }

// 游戏结束
{ "type": "game_over", "result": "correct/wrong/time_out" }

// 玩家加入/离开
{ "type": "player_joined", "player_name": "赵六", "role_name": "管家" }
{ "type": "player_left", "player_name": "赵六" }

// 角色分配
{ "type": "role_assigned", "role": { ... }, "secret": { ... } }
```

## 7. LLM 主持人系统 Prompt

LLM DM 的系统 prompt 分为两个阶段：

### 阶段 A：剧本生成

生成完整剧本（角色、线索、真凶、作案手法、背景故事），沿用现有 prompt 逻辑但优化结构。

### 阶段 B：游戏主持

```
你是一名剧本杀主持人（DM）。你的职责：

1. 动态发布事件 — 每轮给玩家一个情境或发现
2. 投放线索 — 根据游戏进度和玩家行为决定何时放出什么线索
3. 维持剧情一致性 — 所有事件和线索必须符合剧本设定
4. 引导节奏 — 玩家卡住时给提示，讨论热烈时推进剧情
5. 处理指控 — 当有指控时，宣布进入审判环节
6. 揭晓真相 — 投票达成共识后，完整复盘故事
7. 评价玩家 — 为每个玩家生成表现评价

规则：
- 不要单方面宣布游戏结束（除非超时）
- 所有正常结束必须经过玩家投票
- 线索投放要有节奏感，不要一次性全部放出
- 给不同角色投放个性化线索（利用 target_role）
- 保持悬疑感和趣味性
```

## 8. 前端组件设计

### 8.1 页面/组件

| 组件 | 功能 |
|---|---|
| `RoomList` | 房间列表 + 创建房间 |
| `RoomJoin` | 输入玩家名 + 加入房间 |
| `WaitingLobby` | 等待玩家加入，显示已加入玩家和角色 |
| `RoleCard` | 角色卡展示（公开展示 + 秘密任务） |
| `ChatPanel` | 公共聊天 + 私聊切换 |
| `EventDisplay` | LLM 事件/线索展示区域 |
| `AccusationPanel` | 指控面板（选择嫌疑人 + 写理由） |
| `VotePanel` | 投票面板 |
| `TrialPanel` | 审判环节（展示所有指控 + 辩论） |
| `RevealPanel` | 真相揭晓 + 玩家评价 |
| `GameTimer` | 游戏倒计时 |
| `HostStatus` | LLM DM 状态指示 |

### 8.2 页面流转

```
RoomList → RoomJoin → WaitingLobby → RoleCard(逐个阅读)
  ↓
[主游戏界面] = EventDisplay + ChatPanel + AccusationPanel + VotePanel + GameTimer
  ↓ (指控触发)
TrialPanel (覆盖主界面)
  ↓ (投票达成)
RevealPanel
  ↓
RoomList (返回)
```

## 9. 项目结构

```
剧本杀/
├── server/                      # FastAPI 后端
│   ├── main.py                  # 应用入口
│   ├── config.py                # 配置 (.env)
│   ├── llm_client.py            # LLM API 客户端（沿用现有）
│   ├── models.py                # 数据模型（重写为 Pydantic）
│   ├── game_manager.py          # 游戏状态管理
│   ├── host_dm.py               # LLM 主持人逻辑
│   ├── websocket_hub.py         # WebSocket 房间管理
│   ├── api_routes.py            # REST API 路由
│   └── middleware.py            # 中间件
│
├── client/                      # Vue 3 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── stores/
│   │   │   └── game.ts          # WebSocket 状态管理 (Pinia)
│   │   ├── components/
│   │   │   ├── RoomList.vue
│   │   │   ├── RoomJoin.vue
│   │   │   ├── WaitingLobby.vue
│   │   │   ├── RoleCard.vue
│   │   │   ├── ChatPanel.vue
│   │   │   ├── EventDisplay.vue
│   │   │   ├── AccusationPanel.vue
│   │   │   ├── VotePanel.vue
│   │   │   ├── TrialPanel.vue
│   │   │   ├── RevealPanel.vue
│   │   │   ├── GameTimer.vue
│   │   │   └── HostStatus.vue
│   │   ├── types/
│   │   │   └── ws.ts            # WebSocket 消息类型定义
│   │   └── utils/
│   │       └── ws.ts            # WebSocket 连接管理
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── shared/                      # 共享类型/Schema
│   └── schemas.ts               # 前后端共享的 Zod/Pydantic 校验规则
│
├── tests/                       # 测试
│   └── test_game_manager.py
│
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-22-redesign-design.md
│
├── .env                         # 配置（gitignored）
├── .env.example                 # 配置模板
├── requirements.txt             # Python 依赖
└── README.md
```

## 10. 依赖

### 后端

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.0
python-dotenv>=1.0.0
requests>=2.31.0          # LLM API 调用
httpx>=0.28.0             # 异步 HTTP（备选）
```

### 前端

```
vue@^3.5.0
typescript@^5.6.0
pinia@^2.2.0
vite@^6.0.0
```

## 11. 与旧代码的关系

| 旧模块 | 新方案 | 处理方式 |
|---|---|---|
| `main.py` | 废弃 | 不再需要 |
| `config.py` | `server/config.py` | 沿用逻辑，重写 |
| `models.py` | `server/models.py` | 重写为 Pydantic 模型 |
| `game_manager.py` | `server/game_manager.py` | 重写，适配 WebSocket |
| `llm_client.py` | `server/llm_client.py` | **直接沿用**，几乎不用改 |
| `ui/` | `client/src/components/` | 全部重写为 Vue 组件 |
| `GameThread` | WebSocket 服务端推送 | 不再需要 QThread |
| `requirements.txt` | `requirements.txt` | 替换为 FastAPI 依赖 |

**可复用：** `llm_client.py`（LLM API 调用逻辑）基本可以直接搬过来。

## 12. 风险与注意事项

1. **LLM 响应延迟** — WebSocket 推送需要等待 LLM 生成，需要显示"主持人正在思考..."状态，设置超时
2. **LLM 剧情一致性** — 系统 prompt 需要足够强约束，每轮传递完整上下文
3. **浏览器 WebSocket 兼容性** — 主流浏览器都支持，无需 Polyfill
4. **局域网连接** — 服务器绑定 `0.0.0.0`，客户端通过 `http://SERVER_IP:8000` 访问
5. **无数据库** — 游戏数据全在内存，服务器重启丢失。如果需要存档，用 JSON 文件持久化
