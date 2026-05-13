# System Fixes - Batch Startup/Stop and UI Improvements

**Date:** 2026-05-13  
**Author:** OpenCode  
**Status:** ✅ Complete

## Overview

This document describes a batch of system fixes addressing critical issues with the Script Murder application:

1. LLM configuration page accessibility
2. UI layout overlap issues
3. Database duplicate cleanup
4. Batch script reliability

## Problem Summary

### 1. LLM Configuration Page Not Accessible
- **Issue:** Clicking "LLM 配置" in sidebar had no effect
- **Root Cause:** `/settings` route did not exist
- **Impact:** Users could not configure LLM from main navigation

### 2. RoomCreate Layout Overlap
- **Issue:** Input fields overlapped with collapsible sidebar (80px width)
- **Root Cause:** `margin: 40px auto` centered content without accounting for sidebar
- **Impact:** Poor UX, input fields partially hidden

### 3. Database Duplicate Scripts
- **Issue:** 101 duplicate test scripts accumulated in database
- **Root Cause:** Repeated testing created duplicates without cleanup
- **Impact:** Cluttered UI, slow queries, confusion

### 4. Batch Script Crashes
- **Issue:** `stop.bat` crashed when executed
- **Root Cause:** PowerShell multi-line syntax errors and missing error handling
- **Impact:** Users could not cleanly stop servers, needed manual process killing

## Solutions Implemented

### 1. LLMConfigPage Component

**File:** `client/src/components/LLMConfigPage.vue`

Standalone full-page LLM configuration component:
- API endpoint input with auto-completion hint
- Model selection (dropdown + manual input)
- API key input with show/hide toggle
- Fetch models button (`/v1/models`)
- Test connection button (`/api/llm/providers/default/test`)
- Save config button (`/api/llm/providers`)
- Status indicators (connected/failed)
- Error and success messages

**Route:** Added to `client/src/router.ts`:
```typescript
{ path: '/settings', component: () => import('./components/LLMConfigPage.vue') }
```

**Utility:** Extracted `normalizeEndpoint()` to `client/src/utils/endpoint.ts` for reuse.

### 2. RoomCreate Layout Fix

**File:** `client/src/pages/RoomCreate.vue`

Changed CSS from:
```css
.room-create {
  max-width: 600px;
  margin: 40px auto;
  padding: var(--space-2xl);
}
```

To:
```css
.room-create {
  max-width: 600px;
  margin: 40px 40px 40px 120px; /* top right bottom left */
  padding: var(--space-2xl);
}
```

**Rationale:** 120px left margin clears the 80px sidebar with 40px breathing room.

### 3. Duplicate Cleanup Tool

**File:** `server/scripts/cleanup_duplicates.py`

Python script that:
- Connects to `scripts.db`
- Detects duplicates by (title, genre, player_count)
- Keeps most recent version (by created_at)
- Soft deletes older versions (sets `is_active = 0`)
- Interactive mode with confirmation prompts
- Non-interactive mode (`--non-interactive` flag) for automation

**Execution:**
```bash
python server/scripts/cleanup_duplicates.py
# or
python server/scripts/cleanup_duplicates.py --non-interactive
```

**Results:** Cleaned 101 duplicate scripts across 7 groups.

### 4. Batch Script Rewrite

#### stop.bat

**Old Issues:**
- Multi-line PowerShell syntax errors
- No error handling
- No process name display
- Silent failures

**New Features:**
- Proper try/catch error handling
- Process name display for clarity
- Graceful handling of missing processes
- Clear status messages (green/yellow/red)
- UTF-8 encoding support

**Key Improvements:**
```powershell
try {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop
    if ($conn) {
        $processId = $conn.OwningProcess
        $process = Get-Process -Id $processId
        Stop-Process -Id $processId -Force
        Write-Host "已停止端口 $port (进程：$processId - $($process.ProcessName))"
    }
} catch {
    Write-Host "检查端口 $port 时出错：$_" -ForegroundColor Red
}
```

#### start.bat

**Old Issues:**
- Single-line PowerShell command (hard to read/debug)
- No progress feedback
- Silent dependency checks

**New Features:**
- Multi-line readable PowerShell
- Step-by-step progress indicators
- Environment check with version display
- Dependency installation with status
- Clear success/failure messages
- UTF-8 encoding support

**Key Improvements:**
```powershell
Write-Host '检查环境...' -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host '  ✗ Python 未安装' -ForegroundColor Red
    exit 1
}
```

## Testing

### Build Verification
```bash
cd client && npm run build
# ✓ built in 2.48s
```

### Test Suite
```bash
cd client && npm test
# Test Files  8 passed (8)
# Tests       91 passed (91)
```

### Database Cleanup
```bash
python server/scripts/cleanup_duplicates.py --non-interactive
# ✅ 清理完成！共删除 101 个重复剧本
```

## Files Changed

| File | Type | Description |
|------|------|-------------|
| `client/src/components/LLMConfigPage.vue` | NEW | Standalone LLM config page |
| `client/src/utils/endpoint.ts` | NEW | Endpoint normalization utility |
| `client/src/router.ts` | MODIFIED | Added `/settings` route |
| `client/src/pages/RoomCreate.vue` | MODIFIED | Fixed left margin (120px) |
| `server/scripts/cleanup_duplicates.py` | NEW | Duplicate cleanup tool |
| `stop.bat` | REWRITE | Robust PowerShell syntax |
| `start.bat` | REWRITE | Better progress feedback |

## Design Principles Applied

1. **Isolation:** Each fix is independent and testable
2. **Safety:** Soft deletes instead of hard deletes for data preservation
3. **User Feedback:** Clear status messages at every step
4. **Error Handling:** Try/catch blocks prevent silent failures
5. **Consistency:** Uses existing design system CSS variables
6. **Reusability:** Extracted `normalizeEndpoint()` utility

## Future Improvements

1. **Automated Cleanup:** Schedule periodic duplicate cleanup
2. **Duplicate Prevention:** Add unique constraints in database schema
3. **Batch Script Logging:** Write logs to file for debugging
4. **Health Check Endpoint:** Add `/health` for monitoring
5. **Process Management:** Consider using PM2 or similar for production

## Migration Notes

- No database migration required (soft deletes are reversible)
- No API changes
- Frontend backward compatible
- Batch scripts are drop-in replacements

## Rollback Plan

If issues arise:
1. Restore batch scripts from git history
2. Re-run cleanup tool in reverse (manually re-enable soft-deleted scripts)
3. Remove `/settings` route if LLMConfigPage causes problems

## Success Criteria

- ✅ LLM config accessible via sidebar navigation
- ✅ RoomCreate layout no longer overlaps with sidebar
- ✅ Database cleaned of 101 duplicate scripts
- ✅ stop.bat executes without crashes
- ✅ start.bat provides clear progress feedback
- ✅ All tests pass (91/91)
- ✅ Build succeeds without errors
