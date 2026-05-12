# 剧本杀项目开发工作流

📍 **位置**: `C:\Users\Flex\Desktop\Codes\剧本杀\docs\opencode\workflow.md`

本文件定义剧本杀项目的标准开发工作流。

---

## 🔄 完整开发流程

### 1. 需求阶段

```mermaid
graph LR
    A[用户故事] --> B[功能规格]
    B --> C[技术方案]
    C --> D[风险评估]
```

**输入**: 用户故事或功能需求  
**输出**: 明确的功能规格和技术方案

**示例**:
```
用户故事: "作为玩家，我想投票选择嫌疑人"

功能规格:
- 玩家可以对任意玩家投票
- 显示投票进度（不显示具体投票）
- 达到 50% 阈值后自动揭示结果
- 投票不可撤销

技术方案:
- POST /api/rooms/{id}/vote (API)
- VotePanel.vue (前端组件)
- WebSocket vote_cast, vote_progress (实时)
```

### 2. 设计阶段 (brainstorming)

**调用技能**: `skill: "brainstorming"`

**流程**:
1. 探索项目上下文
2. 提出澄清问题（一次一个）
3. 提出 2-3 种方案及权衡
4. 呈现设计方案
5. 用户批准

**输出**: 设计文档 (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`)

### 3. 计划阶段 (writing-plans)

**调用技能**: `skill: "writing-plans"`

**流程**:
1. 基于设计创建实施计划
2. 分解为具体任务
3. 定义检查点和验收标准

**输出**: 详细的实施计划

### 4. 实施阶段 (subagent-driven-development)

**调用技能**: `skill: "subagent-driven-development"`

**并行任务示例**:

```typescript
// 后端实施
Task(
  description: "实现投票 API",
  prompt: `
    根据设计文档实施：
    - POST /api/rooms/{id}/vote
    - WebSocket vote_cast 广播
    - 投票计数和阈值检查
    - 单元测试
    
    参考：docs/superpowers/specs/voting-design.md
  `,
  subagent_type: "python-pro"
)

// 前端实施
Task(
  description: "实现投票组件",
  prompt: `
    根据设计文档实施：
    - VotePanel.vue 组件
    - WebSocket 监听 vote_progress
    - 投票提交表单
    - 组件测试
    
    参考：docs/superpowers/specs/voting-design.md
  `,
  subagent_type: "vue-expert"
)
```

### 5. 验证阶段 (verification-before-completion)

**调用技能**: `skill: "verification-before-completion"`

**检查清单**:

```bash
# 类型检查
npx tsc --noEmit  # 退出码 0

# 后端测试
pytest tests/ -v --cov  # 全部通过

# 前端测试
npm test  # 全部通过

# 代码审查
使用 code-reviewer agent
```

### 6. 合并阶段 (finishing-a-development-branch)

**调用技能**: `skill: "finishing-a-development-branch"`

**选项**:
1. **直接合并** - 小改动，测试全部通过
2. **创建 PR** - 主要功能，需要审查
3. **清理分支** - 删除临时文件，更新文档

---

## 📋 日常开发流程

### 早晨启动

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 检查依赖
pip check  # Python
npm audit  # JavaScript

# 3. 运行测试
pytest tests/ -v && npm test

# 4. 启动开发服务器
# 后端：uvicorn server.main:app --reload
# 前端：npm run dev
```

### 功能开发

```bash
# 1. 创建功能分支
git checkout -b feature/voting-system

# 2. 编写测试 (TDD)
pytest tests/test_voting.py::test_vote_cast -v

# 3. 实施功能
# 使用 brainstorming + writing-plans

# 4. 运行测试
pytest tests/test_voting.py -v

# 5. 提交代码
git add .
git commit -m "feat: implement voting system"
git push origin feature/voting-system
```

### 代码审查

```bash
# 1. 创建 Pull Request
gh pr create --title "feat: implement voting system" \
             --body "See design doc: docs/superpowers/specs/voting-design.md"

# 2. 等待审查
# 使用 code-reviewer agent 进行自审

# 3. 处理反馈
# 根据审查意见修改代码

# 4. 合并
gh pr merge --squash --delete-branch
```

---

## 🐛 Bug 修复流程

### 1. 重现问题

```typescript
// 调用技能：systematic-debugging

// 步骤:
1. 收集错误日志和堆栈跟踪
2. 尝试重现问题
3. 记录重现步骤
4. 确定影响范围
```

### 2. 定位原因

```bash
# 使用调试工具
pytest tests/ -v --pdb  # 进入交互式调试

# 或使用日志
logging.basicConfig(level=logging.DEBUG)
logger.debug(f"State: {state}")
```

### 3. 实施修复 (test-driven-development)

```typescript
// 调用技能：test-driven-development

// 步骤:
1. 编写失败测试（重现 bug）
2. 运行测试确认失败
3. 编写最小代码通过测试
4. 重构（保持测试通过）
5. 添加更多测试覆盖边界情况
```

### 4. 验证修复

```bash
# 运行所有测试
pytest tests/ -v && npm test

# 检查类型
npx tsc --noEmit

# 手动测试（如果适用）
```

---

## 📦 发布流程

### 准备发布

```bash
# 1. 更新版本号
# package.json (前端)
# server/__init__.py (后端)

# 2. 更新 CHANGELOG
echo "## [1.2.0] - 2026-05-11" >> CHANGELOG.md
echo "- feat: voting system" >> CHANGELOG.md

# 3. 运行完整测试
pytest tests/ -v --cov && npm test && npm run build

# 4. 创建发布标签
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### 部署到生产

```bash
# 1. 备份数据库
pg_dump script_murder > backup.sql

# 2. 拉取最新代码
git pull origin main

# 3. 安装依赖
pip install -r requirements.txt
cd client && npm install

# 4. 运行迁移
python manage.py migrate

# 5. 构建前端
cd client && npm run build

# 6. 重启服务
systemctl restart script-murder-backend
systemctl restart script-murder-frontend
```

---

## 🎯 最佳实践

### 1. 提交信息规范

```bash
# 格式：<type>(<scope>): <subject>

# 类型:
feat:     新功能
fix:      Bug 修复
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构
test:     测试相关
chore:    构建/工具相关

# 示例:
git commit -m "feat(voting): add vote casting API"
git commit -m "fix(game): correct player count calculation"
git commit -m "docs(api): update voting endpoint documentation"
```

### 2. 分支命名规范

```bash
# 格式：<type>/<description>

feature/voting-system
bugfix/wrong-player-count
docs/api-update
refactor/game-state
```

### 3. 代码风格

**Python (PEP 8)**:
```python
# ✅ 正确
def calculate_vote_percentage(votes: int, total: int) -> float:
    if total == 0:
        return 0.0
    return (votes / total) * 100
```

**TypeScript**:
```typescript
// ✅ 正确
const calculateVotePercentage = (votes: number, total: number): number => {
  if (total === 0) return 0;
  return (votes / total) * 100;
};
```

### 4. 文档更新

**每次功能改动必须更新**:
- API 文档 (`docs/api-reference.md`)
- README (如果影响使用方式)
- 组件注释 (如果 API 变化)

---

## 📊 性能监控

### 后端监控

```python
# 1. 请求耗时
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {duration:.3f}s")
    return response

# 2. 数据库查询耗时
@app.on_event("startup")
async def setup_db_monitor():
    app.state.db_pool = await asyncpg.create_pool(
        ...
        statement_cache_size=100  # 缓存预编译语句
    )
```

### 前端监控

```typescript
// 1. 组件渲染耗时
import { onMounted, onUnmounted } from 'vue';

let startTime: number;
onMounted(() => {
  startTime = performance.now();
  onUnmounted(() => {
    const duration = performance.now() - startTime;
    console.log(`Component rendered in ${duration}ms`);
  });
});

// 2. WebSocket 连接状态
const wsStatus = ref('connecting');
watch(wsStatus, (status) => {
  logger.info(`WebSocket status: ${status}`);
});
```

---

## 🔗 相关资源

- [项目规则](./project-rules.md)
- [全局开发规范](C:\Users\Flex\.config\opencode\rules\development.md)
- [Subagent 使用指南](C:\Users\Flex\.config\opencode\rules\subagent-guide.md)

---

**最后更新**: 2026-05-11  
**版本**: v1.0
