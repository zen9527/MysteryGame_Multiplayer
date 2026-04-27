# 🎭 剧本杀 - LLM 驱动多人在线版

基于 FastAPI + Vue 3 的 Web 版谋杀之谜游戏系统，由本地 LLM 自动担任 DM 主持人。

## ✨ 特性

- **多人在线** — WebSocket 实时通信，局域网即可开局
- **LLM 全权主持** — 自动生成剧本、角色卡、线索、复盘总结
- **6 种剧本类型** — 悬疑推理 / 古风权谋 / 现代都市 / 恐怖惊悚 / 欢乐搞笑 / 科幻未来
- **完整游戏流程** — 选本 → 生成剧本 → 阅读角色卡 → 自我介绍 → 搜证 → 讨论 → 投票 → 审判 → 揭晓 → 复盘
- **信息隔离** — 角色卡分层解锁（3 层），DM 私信，个人线索，公共/私人信息严格隔离
- **公聊 + 私聊** — 全局讨论与玩家间一对一私聊，DM 可向特定玩家发送私信
- **审判系统** — accusation + 多轮投票 + 真相揭晓
- **断线重连** — WS 重连自动恢复角色卡、线索、私信和聊天历史

## 🚀 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r requirements.txt

# 前端
cd client
npm install
```

### 2. 配置 LLM 服务器

编辑 `.env` 文件（如不存在则创建）：

```ini
LLM_ENDPOINT=http://192.168.1.107:12340
LLM_API_KEY=your_api_key_here
LLM_MODEL=qwen/qwen3.6-35b-a3b
```

### 3. 启动

```bash
# 使用启动脚本
start.bat

# 或手动启动
# 后端
uvicorn server.main:app --host 0.0.0.0 --port 8000

# 前端
cd client
npm run dev
```

打开浏览器访问 `http://localhost:3000`。

## 📁 项目结构

```
剧本杀/
├── server/                    # FastAPI 后端
│   ├── main.py                # 应用入口
│   ├── config.py              # 配置管理
│   ├── llm_client.py          # LLM API 客户端
│   ├── models.py              # Pydantic 数据模型
│   ├── game_manager.py        # 游戏状态管理
│   ├── host_dm.py             # LLM 主持人逻辑
│   ├── websocket_hub.py       # WebSocket 房间管理
│   ├── api_routes.py          # REST API 路由
│   └── middleware.py          # CORS 中间件
│
├── client/                    # Vue 3 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router.ts          # Vue Router 路由配置
│   │   ├── stores/game.ts     # Pinia 状态管理（角色卡、私信、线索、公聊、去重）
│   │   ├── types/ws.ts        # WebSocket 类型定义
│   │   ├── utils/ws.ts        # WebSocketManager（已废弃 — GamePage 使用直连 WS）
│   │   └── components/        # 11 个组件
│   │       ├── GamePage.vue           # 主游戏页面（左：公聊/事件，右：Tab 导航）
│   │       ├── RoleCard.vue           # 角色卡（分层解锁 + 折叠）
│   │       ├── PrivateChatPanel.vue   # DM 私信面板
│   │       ├── ClueCardPanel.vue      # 线索卡片（展开/折叠）
│   │       ├── WaitingLobby.vue       # 等待大厅
│   │       ├── RoomList.vue           # 房间列表
│   │       ├── RoomJoin.vue           # 加入房间
│   │       ├── GameTimer.vue          # 倒计时组件
│   │       ├── AdminPanel.vue         # 管理员面板
│   │       ├── ScriptEditor.vue       # 剧本编辑器
│   │       └── ChatPanel.vue          # 聊天面板（遗留组件）
│   └── tests/                 # 前端组件测试
│
├── shared/                    # 共享类型/Schema
│   ├── ws_types.py            # 后端 Pydantic 校验
│   └── schemas.ts             # 前端 Zod 校验
│
├── tests/                     # 后端单元测试 & 集成测试
├── requirements.txt           # Python 依赖
└── .gitignore
```

## 🧪 运行测试

```bash
# 后端测试
pytest tests/ -v

# 前端测试
cd client
npm test
```

## 📄 许可证

本项目仅供学习和研究使用。

---

**作者**: Flex  
**版本**: v5.0.0  
**最近更新**: 信息隔离系统 + 断线重连 + 聊天去重
