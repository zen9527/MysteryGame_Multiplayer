# Phase 3: 剧本编辑与导入导出功能实施计划

## 概述
Phase 3 专注于剧本的生命周期管理：编辑、导入、导出和版本控制。这将使剧本库更加实用，支持用户自定义内容和数据迁移。

---

## 功能需求

### 1. 剧本编辑器 (Script Editor)
**优先级**: 高  
**描述**: 提供完整的剧本编辑界面，支持所有字段的增删改查

#### 子功能
- **1.1 富文本编辑**: 支持背景故事、角色描述等字段的富文本编辑
- **1.2 字段管理**: 
  - 剧本元数据（标题、类型、难度、人数、预计时间）
  - 背景故事
  - 角色管理（增删改角色，包含所有角色字段）
  - 线索管理（分 Act 的线索编辑）
  - NPC 管理
  - 时间线编辑
  - 关系图谱
- **1.3 实时验证**: 表单验证（必填字段、数据格式）
- **1.4 自动保存**: 防抖动的自动保存功能（30s 间隔）
- **1.5 撤销/重做**: 操作历史记录

#### 技术实现
```typescript
// 前端组件结构
client/src/components/scripts/
  ScriptEditor.vue          # 主编辑器组件
  EditorToolbar.vue         # 工具栏（保存、撤销、导出等）
  RoleEditor.vue            # 角色编辑表单
  ClueEditor.vue            # 线索编辑表单
  TimelineEditor.vue        # 时间线编辑
  RelationshipEditor.vue    # 关系图谱编辑

// 后端 API
server/api/scripts.py
  PUT /api/scripts/{id}     # 更新剧本
  DELETE /api/scripts/{id}  # 删除剧本
```

### 2. 导入/导出功能 (Import/Export)
**优先级**: 高  
**描述**: 支持多种格式的剧本导入和导出

#### 子功能
- **2.1 JSON 导出**: 完整剧本数据导出为 JSON 文件
- **2.2 JSON 导入**: 从 JSON 文件导入剧本（支持覆盖/合并）
- **2.3 PDF 导出**: 生成可读性强的 PDF 文档（用于打印/分享）
- **2.4 Markdown 导出**: 生成 Markdown 格式（便于版本控制）
- **2.5 批量导入**: 支持一次性导入多个剧本

#### 技术实现
```typescript
// 前端
client/src/utils/export.ts
  exportToJSON(script: ScriptV2): Blob
  exportToPDF(script: ScriptV2): Blob
  exportToMarkdown(script: ScriptV2): string
  
client/src/components/scripts/
  ImportDialog.vue          # 导入对话框（文件选择、格式检测）
  ExportDialog.vue          # 导出对话框（格式选择、选项）

// 后端
server/api/scripts.py
  POST /api/scripts/import   # 批量导入
  GET /api/scripts/{id}/export/pdf  # PDF 导出
  GET /api/scripts/{id}/export/json # JSON 导出
```

### 3. 版本管理 (Version Control)
**优先级**: 中  
**描述**: 跟踪剧本的历史版本，支持回滚和对比

#### 子功能
- **3.1 版本历史**: 显示剧本的所有修改历史
- **3.2 版本对比**: 并排对比两个版本的差异
- **3.3 版本回滚**: 恢复到任意历史版本
- **3.4 版本标签**: 为重要版本添加标签（如"v1.0 正式版"）
- **3.5 自动版本**: 定期自动创建版本快照

#### 技术实现
```typescript
// 数据库模型
server/models.py
  class ScriptVersion(BaseModel):
    id: str
    script_id: str
    version_number: int
    data: ScriptV2  # 完整的剧本数据
    created_at: datetime
    created_by: str
    notes: str  # 版本说明

// 后端 API
server/api/scripts.py
  GET /api/scripts/{id}/versions      # 获取版本列表
  GET /api/scripts/{id}/versions/{version_id}  # 获取特定版本
  POST /api/scripts/{id}/versions/{version_id}/restore  # 恢复版本
  GET /api/scripts/{id}/versions/compare  # 对比版本

// 前端组件
client/src/components/scripts/
  VersionHistory.vue        # 版本历史列表
  VersionDiff.vue           # 版本对比视图
  VersionRestoreDialog.vue  # 版本回滚确认
```

---

## 实施步骤

### Step 1: 剧本编辑器 (预计 2-3 天)
1. **Day 1**: 
   - [ ] 创建基础编辑器布局（左侧角色列表，右侧编辑区域）
   - [ ] 实现元数据编辑表单
   - [ ] 添加表单验证逻辑

2. **Day 2**:
   - [ ] 实现角色编辑器（增删改角色）
   - [ ] 实现线索编辑器（分 Act 管理）
   - [ ] 添加自动保存功能

3. **Day 3**:
   - [ ] 实现 NPC、时间线、关系编辑
   - [ ] 添加撤销/重做功能
   - [ ] 编写单元测试

### Step 2: 导入导出功能 (预计 1-2 天)
1. **Day 1**:
   - [ ] 实现 JSON 导入/导出
   - [ ] 添加文件拖拽支持
   - [ ] 实现导入冲突处理（覆盖/合并）

2. **Day 2**:
   - [ ] 集成 PDF 生成库（如 `jspdf` + `html2canvas`）
   - [ ] 设计 PDF 模板（美观的排版）
   - [ ] 实现 Markdown 导出

### Step 3: 版本管理 (预计 1-2 天)
1. **Day 1**:
   - [ ] 创建数据库迁移（ScriptVersion 表）
   - [ ] 实现版本 CRUD API
   - [ ] 添加自动版本快照功能

2. **Day 2**:
   - [ ] 实现版本历史 UI
   - [ ] 实现版本对比功能（使用 `diff-match-patch`）
   - [ ] 实现版本回滚

### Step 4: 测试与优化 (预计 1 天)
- [ ] 编写集成测试
- [ ] 性能优化（大剧本的加载和保存）
- [ ] UX 优化（加载状态、错误提示）
- [ ] 文档更新

---

## 技术栈选择

### 前端
- **富文本编辑器**: TipTap 或 Quasar Editor（轻量、Vue 友好）
- **PDF 生成**: `jspdf` + `html2canvas` 或 `pdfmake`
- ** diff 对比**: `diff-match-patch` 或 `jsondiffpatch`
- **文件处理**: `file-saver` + `uuid`

### 后端
- **PDF 生成**: `weasyprint` 或 `reportlab`
- **版本存储**: SQLite（JSON 字段存储完整数据）
- **文件上传**: `python-multipart` + 临时存储

---

## API 设计

### 更新剧本
```http
PUT /api/scripts/{id}
Content-Type: application/json

{
  "title": "新的标题",
  "genre": "悬疑推理",
  "difficulty": "困难",
  "player_count": 6,
  "estimated_time": 120,
  "background_story": "...",
  "roles": [...],
  "clues": [...],
  "npcs": [...],
  "timeline": [...],
  "relationships": [...]
}

Response: 200 OK
{
  "id": "script-123",
  "updated_at": "2026-01-15T10:30:00Z",
  "version": 2
}
```

### 导入剧本
```http
POST /api/scripts/import
Content-Type: multipart/form-data

file: <script.json>
mode: "overwrite" | "merge"  // 可选，默认 overwrite

Response: 201 Created
{
  "imported_count": 1,
  "scripts": [{"id": "script-456", "title": "导入的剧本"}]
}
```

### 获取版本历史
```http
GET /api/scripts/{id}/versions

Response: 200 OK
{
  "versions": [
    {
      "version_id": "v1",
      "version_number": 1,
      "created_at": "2026-01-14T08:00:00Z",
      "created_by": "admin",
      "notes": "初始版本"
    },
    {
      "version_id": "v2",
      "version_number": 2,
      "created_at": "2026-01-15T10:30:00Z",
      "created_by": "admin",
      "notes": "修复角色描述错误"
    }
  ]
}
```

---

## 数据库迁移

### ScriptVersion 表
```sql
CREATE TABLE script_versions (
    id TEXT PRIMARY KEY,
    script_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    data JSON NOT NULL,  -- 完整的 ScriptV2 数据
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    notes TEXT,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
);

CREATE INDEX idx_script_versions_script_id ON script_versions(script_id);
CREATE INDEX idx_script_versions_created_at ON script_versions(created_at DESC);
```

---

## 测试计划

### 单元测试
- [ ] 编辑器表单验证测试
- [ ] 导入/导出格式测试
- [ ] 版本对比算法测试

### 集成测试
- [ ] 完整编辑流程（创建 → 编辑 → 保存 → 验证）
- [ ] JSON 导入导出循环测试
- [ ] 版本回滚测试

### E2E 测试 (Playwright)
- [ ] 剧本编辑完整流程
- [ ] 文件拖拽导入
- [ ] PDF 导出验证

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大剧本性能问题 | 高 | 分页加载、虚拟滚动、Web Worker 处理 |
| PDF 排版复杂 | 中 | 使用成熟库、提供模板选项 |
| 版本数据膨胀 | 中 | 定期清理旧版本、压缩存储 |
| 导入冲突处理 | 低 | 清晰的 UI 提示、预览机制 |

---

## 验收标准

### 剧本编辑器
- ✅ 可以编辑所有剧本字段
- ✅ 支持增删角色和线索
- ✅ 表单验证正常工作
- ✅ 自动保存不丢失数据
- ✅ 撤销/重做功能正常

### 导入导出
- ✅ JSON 导入导出完整数据
- ✅ PDF 导出排版美观
- ✅ 文件拖拽工作正常
- ✅ 批量导入支持多个文件

### 版本管理
- ✅ 显示完整的版本历史
- ✅ 版本对比清晰可见
- ✅ 回滚功能正常工作
- ✅ 自动版本快照定期创建

---

## 下一步行动

1. **立即开始**: Step 1 Day 1 - 创建基础编辑器布局
2. **依赖检查**: 确认 TipTap/Quasar Editor 安装
3. **设计评审**: 确认编辑器 UI 设计（可使用 `/design-shotgun`）
4. **数据库迁移**: 提前创建 ScriptVersion 表迁移文件
