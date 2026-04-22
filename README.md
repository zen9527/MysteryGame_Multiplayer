# 🎭 剧本杀 - LLM 驱动单机版

基于 PyQt6 + Python 的完全重构版本，由本地 LLM 自动主持的谋杀之谜游戏系统。

## ✨ 特性

- **完整游戏流程**：从选本到复盘的 8 个阶段全部实现
- **LLM 自动生成**：根据玩家人数和剧本分类自动生成完整剧本
- **逐个阅读角色卡**：DM 控制，玩家只能看到自己的秘密
- **搜证系统**：多阶段线索解锁、红鲱鱼（误导线索）机制
- **公聊 + 私聊**：完整的讨论环节支持
- **多轮投票**：支持平票处理和最终揭晓
- **复盘总结**：真相揭示、关键证据对比

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 LLM 服务器

编辑 `.env` 文件：

```ini
LLM_SERVER_URL=http://192.168.1.107:12340
LLM_API_KEY=your_api_key_here
LLM_MODEL=model
```

### 3. 启动游戏

```bash
python main.py
# 或使用启动脚本
启动.bat
```

## 📖 游戏流程

1. **玩家加入** - 添加至少 2 名玩家，选择剧本分类
2. **生成剧本** - LLM 自动生成完整剧本（约 2-5 分钟）
3. **阅读角色卡** - DM 逐个分配，玩家单独阅读自己的角色
4. **自我介绍** - 每位玩家介绍角色背景和关系
5. **搜证环节** - 多阶段解锁线索，可以公开或私聊取证
6. **讨论环节** - 公聊（所有人可见）+ 私聊（一对一）
7. **投票环节** - 多轮投票选出凶手
8. **复盘揭晓** - DM 揭示真相

## 📁 项目结构

```
剧本杀/
├── main.py                      # 入口点
├── config.py                    # 配置管理（.env 文件）
├── models.py                    # 数据模型
├── game_manager.py              # 游戏状态管理
├── llm_client.py                # LLM API 客户端
│
├── ui/                          # UI 组件包
│   ├── main_window.py           # 主窗口
│   └── widgets/                 # UI 组件
│       ├── waiting_stage.py     # 等待阶段
│       ├── generating_stage.py  # 剧本生成中
│       ├── reading_roles_stage.py    # 阅读角色卡
│       ├── self_introduction_stage.py # 自我介绍
│       ├── evidence_search_stage.py   # 搜证系统
│       ├── discussion_stage.py      # 讨论环节
│       ├── voting_stage.py          # 投票系统
│       └── review_stage.py          # 复盘揭晓
│
├── tests/                       # 测试用例
│   └── test_all.py              # 100+ 测试，74% 覆盖率
│
├── docs/                        # 文档
│   ├── PROJECT_STRUCTURE.md     # 项目结构说明
│   ├── REFACTORING_REPORT.md    # 重构报告
│   └── DEVELOPMENT_REPORT.md    # 开发报告
│
├── assets/                      # 资源文件（图片、音效等）
│
├── .env                         # 本地配置（API Key）
├── requirements.txt             # 依赖列表
├── .gitignore                   # Git 忽略文件
└── 启动.bat                     # Windows 启动脚本
```

## 🧪 运行测试

```bash
pytest tests/test_all.py -v --cov=. --cov-report=term-missing
```

## 📚 文档

- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [重构报告](docs/REFACTORING_REPORT.md)
- [开发报告](docs/DEVELOPMENT_REPORT.md)

## 🔮 未来计划

- [ ] 完善存档/读档功能
- [ ] LLM 辅助 DM（自动生成复盘总结）
- [ ] 多人在线模式（WebSocket）
- [ ] 剧本编辑器
- [ ] 音效和背景音乐支持

## 📄 许可证

本项目仅供学习和研究使用。

---

**作者**: Flex  
**版本**: v2.0.0
