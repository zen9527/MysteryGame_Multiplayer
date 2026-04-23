# 主持人系统设计 — LLM DM + 管理员控制

## 核心角色分工

| 角色 | 职责 | 身份标识 |
|------|------|---------|
| **LLM (DM)** | 全自动推进故事、生成事件/线索、判断阶段转换时机 | 系统内部，无UI |
| **管理员** | 房间创建者，剧本初始化、玩家管理、紧急控制 | `room_creator_id` + WebSocket标签 |
| **玩家** | 普通参与者，聊天、指控、投票 | 普通连接 |

## 游戏前：管理员控制面板（WaitingLobby 扩展）

```
创建房间 → 进入 WaitingLobby（管理员视图）
   │
   ├─ 1. 选择剧本类型（6种下拉菜单）+ 难度 + 预计时长
   ├─ 2. 点击"生成剧本" → LLM 生成完整剧本
   ├─ 3. 预览剧本内容（背景故事、角色列表、线索等）
   │      └─ 可编辑修改 / 点"重新生成"
   ├─ 4. 点击"确认剧本" → 保存到房间状态
   └─ 5. 等待玩家加入 → ≥2人时"开始游戏"按钮亮起
```

管理员额外功能（始终可见）：
- 玩家列表 + 踢人按钮
- LLM 连接测试按钮（显示响应时间/状态）
- 房间设置（密码保护、最大人数）

## 游戏中：LLM DM 全自动推进

### 混合阶段架构

```
┌─────────────────────────────────────────────┐
│  第一幕：背景介绍 (固定)                      │
│  LLM生成: 开场事件 → 角色秘密分发 → 初始线索   │
├─────────────────────────────────────────────┤
│  第二幕：自由调查 (LLM动态控制节奏)            │
│  LLM根据玩家聊天自动推送:                     │
│    - 新线索发现                               │
│    - NPC对话/事件                             │
│    - 时间推进提示                             │
│    - 触发条件满足时建议进入审判                │
├─────────────────────────────────────────────┤
│  第三幕：审判揭晓 (固定)                      │
│  LLM生成: 指控辩论 → 投票统计 → 真相揭晓       │
│         → 玩家评价                            │
└─────────────────────────────────────────────┘
```

### LLM 自动推进机制

- WebSocket 监听玩家聊天消息
- LLM 后台分析对话内容，判断是否需要推送事件
- 事件通过 WebSocket 实时广播给所有玩家
- 管理员可以看到 LLM 的"思考日志"（调试面板）

## 管理员紧急控制（游戏进行中）

在 GamePage 中，管理员额外看到一个 **控制面板**：

| 按钮 | 功能 |
|------|------|
| ⏭️ **推进剧情** | 手动触发 LLM 生成下一个事件（覆盖自动模式） |
| 🔍 **追加线索** | 输入自定义线索内容，立即发布 |
| ⚖️ **强制审判** | 跳过剩余调查时间，直接进入第三幕 |
| 🛑 **提前结束** | 立即揭晓真相，游戏结束 |
| 👥 **玩家管理** | 踢人 / 静音 / 查看私聊记录 |
| 📋 **DM日志** | 查看 LLM 的完整推理过程（调试用） |

## 技术架构

### 新增 API 端点

```
POST /api/rooms/{id}/generate-script   # 触发LLM生成剧本（仅管理员）
POST /api/rooms/{id}/dm/push-event     # 手动推进剧情（仅管理员）
POST /api/rooms/{id}/dm/add-clue       # 追加自定义线索（仅管理员）
POST /api/rooms/{id}/force-trial       # 强制进入审判（仅管理员）
POST /api/rooms/{id}/end-game          # 提前结束游戏（仅管理员）
POST /api/rooms/{id}/players/{pid}/kick # 踢出玩家（仅管理员）
GET  /api/dm/log/{id}                  # DM推理日志（仅管理员）
POST /api/test-llm                     # LLM连接测试
```

### GameManager 变更

- `GameState` 新增字段：`room_creator_id: str`、`dm_log: list[str]`、`act: int`（1/2/3）
- `create_game()` 接收 `creator_id` 参数
- 新增方法：`force_trial()`, `end_game()`, `kick_player()`, `push_event()`, `add_clue()`

### HostDM 改造

- 从被动调用改为**自动推进循环**（asyncio.Task）
- 监听 WebSocketHub 的玩家消息事件
- 根据当前阶段和对话内容自动生成事件
- 所有 LLM 输出记录到 `dm_log`

### WebSocketHub 完善

- 实现消息路由：玩家聊天 → GameManager → HostDM 分析 → 广播事件
- 管理员标签识别（WebSocket connect 时携带）
- 断线重连支持

### 前端组件变更

| 组件 | 变更内容 |
|------|---------|
| **WaitingLobby.vue** | 管理员视图：剧本选择表单 + LLM生成按钮 + 预览/编辑 + 玩家管理 |
| **GamePage.vue** | 管理员额外显示控制面板；所有玩家接收 WebSocket 事件推送 |
| **EventDisplay.vue** | 从空壳改为实际渲染 DM 事件，支持打字机效果 |
| **ChatPanel.vue** | 发送消息同时触发 LLM 分析（通过 WebSocket） |
| **AdminPanel.vue** (新) | 管理员控制面板组件（可嵌入 GamePage） |
| **ScriptEditor.vue** (新) | 剧本预览/编辑组件 |

### 管理员权限验证

```python
# middleware.py 新增
def require_admin(event, game_id):
    player_id = event.context.player_id
    game = manager.get_game(game_id)
    if game.room_creator_id != player_id:
        raise HTTPException(403, "仅管理员可操作")
```

## 6种剧本类型枚举

```python
GENRES = [
    ("悬疑推理", "经典谋杀案，逻辑推理"),
    ("古风权谋", "古代宫廷/江湖，权力斗争"),
    ("现代都市", "当代社会背景，情感纠葛"),
    ("恐怖惊悚", "超自然元素，心理恐惧"),
    ("欢乐搞笑", "轻松幽默，反转结局"),
    ("科幻未来", "赛博朋克/太空，高科技犯罪"),
]
```

## 清理清单

需要删除的文件（空壳/死代码）：
- `client/src/components/VotePanel.vue` — GamePage 内嵌投票功能已覆盖
- `client/components/AccusationPanel.vue` — GamePage 内嵌指控功能已覆盖
- `client/components/TrialPanel.vue` — 改为 GamePage 内嵌审判视图
- `client/components/RevealPanel.vue` — 改为 GamePage 内嵌揭晓视图
- `client/src/utils/ws.ts` — 重写为完整 WebSocket 管理器
- `server/_default_script` — 替换为 LLM 生成流程

需要保留但重写的文件：
- `server/host_dm.py` — 从被动调用改为自动推进循环
- `server/websocket_hub.py` — 实现消息路由
- `server/game_manager.py` — 新增管理员方法和阶段管理
- `server/api_routes.py` — 新增管理员端点 + 权限中间件
- `client/src/components/WaitingLobby.vue` — 扩展为管理员控制面板
- `client/src/components/GamePage.vue` — 添加管理员面板 + WebSocket 集成
- `client/src/components/EventDisplay.vue` — 实现 DM 事件渲染
- `client/src/components/ChatPanel.vue` — 实现 WebSocket 消息发送
