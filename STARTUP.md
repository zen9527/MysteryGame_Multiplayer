# Script Murder - 快速启动指南

## 🚀 启动服务器

### 方式 1：使用 PowerShell 脚本（推荐）

```powershell
# 正常启动（两个独立窗口）
.\start.ps1

# 单窗口模式（前后端日志合并）
.\start-single.ps1

# 重启服务器
.\restart.ps1
```

### 方式 2：使用 BAT 脚本（兼容旧版）

```batch
# 双击运行或命令行执行
start.bat
```

## 🛑 停止服务器

### PowerShell 版本（推荐）

```powershell
.\stop.ps1
```

### BAT 版本（兼容旧版）

```batch
stop.bat
```

## 📋 脚本说明

| 脚本 | 功能 | 特点 |
|------|------|------|
| `start.ps1` | 启动前后端 | 自动检查依赖、创建 .env、双窗口显示日志 |
| `start-single.ps1` | 单窗口模式 | 前后端日志合并，适合调试 |
| `stop.ps1` | 停止所有服务 | 通过端口检测进程，更可靠 |
| `restart.ps1` | 一键重启 | 先 stop 再 start |
| `start.bat` / `stop.bat` | 兼容旧版 | 调用对应的 PowerShell 脚本 |

## 🔧 首次使用

1. **安装依赖**
   - Python 3.10+
   - Node.js 18+

2. **配置 LLM 服务器**
   ```bash
   # 脚本会自动创建 .env 文件
   # 编辑 .env，设置你的 LLM_ENDPOINT
   ```

3. **启动**
   ```powershell
   .\start.ps1
   ```

## 🌐 访问地址

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## ⚠️ 常见问题

### PowerShell 执行策略错误
```powershell
# 设置执行策略（管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 端口被占用
```powershell
# 手动清理端口 8000 和 3000 的进程
.\stop.ps1
```

### 依赖安装失败
```bash
# 后端
pip install -r requirements.txt

# 前端
cd client && npm install
```

## 📝 开发命令

### 后端
```bash
# 启动开发服务器
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

# 运行测试
pytest tests/ -v
```

### 前端
```bash
cd client

# 开发服务器
npm run dev

# 构建
npm run build

# 测试
npm test
```
