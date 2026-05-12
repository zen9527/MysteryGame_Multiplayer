# 阶段 1：核心类型统一实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立从 Database → API → Frontend 的完整类型安全链，消除重复验证逻辑

**Architecture:** 创建共享 Zod schemas 在 shared/schemas/ws.ts，API 层使用 Pydantic 模型（字段与 Zod 一致），前端导入 Zod schemas 进行验证。手动维护两层映射，未来可自动化。

**Tech Stack:** Zod (前端验证), Pydantic v2 (后端验证), TypeScript, FastAPI, Vue 3

---

## File Structure

### 创建文件
- `shared/schemas/ws.ts` - 共享 Zod schemas（chat, clue, role, game state）
- `shared/schemas/__init__.py` - Python shared 包初始化
- `server/models/ws.py` - Pydantic v2 模型（与 Zod schema 字段一致）
- `client/src/utils/schema-validation.ts` - 前端验证工具函数
- `tests/test_schema_validation.py` - Schema 验证单元测试

### 修改文件
- `client/src/types/ws.ts` - 更新为从 shared/schemas 导入类型
- `client/src/stores/game.ts` - 集成 schema 验证
- `server/api/chat.get.ts` (或 equivalent) - 使用 Pydantic 模型验证响应
- `server/api/clue.get.ts` - 使用 Pydantic 模型验证响应
- `shared/ws_types.py` - 标记为 deprecated

---

## Task 1: 创建共享 Zod Schemas

**Files:**
- Create: `shared/schemas/ws.ts`
- Create: `shared/schemas/__init__.py` (empty, for Python package)

- [ ] **Step 1: Write shared Zod schemas file**

```typescript
// shared/schemas/ws.ts
import { z } from "zod";

// Chat Message Schema
export const chatMessageSchema = z.object({
  message_id: z.string(),
  content: z.string().min(1).max(2000),
  player_id: z.string(),
  role_name: z.string(),
  timestamp: z.string().datetime(),
  from_player_name: z.string()
});
export type ChatMessage = z.infer<typeof chatMessageSchema>;

// Clue Schema
export const clueSchema = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string(),
  unlock_phase: z.enum(["act1", "act2"]),
  clue_type: z.enum(["public", "private"]),
  related_role_id: z.string().optional()
});
export type Clue = z.infer<typeof clueSchema>;

// Role Card Schema
export const roleCardSchema = z.object({
  role_id: z.string(),
  role_name: z.string(),
  player_id: z.string(),
  layer: z.number().int().min(1).max(3),
  content: z.string(),
  secrets: z.array(z.string()).optional()
});
export type RoleCard = z.infer<typeof roleCardSchema>;

// Player Schema
export const playerSchema = z.object({
  player_id: z.string(),
  role_id: z.string(),
  role_name: z.string(),
  is_admin: z.boolean()
});
export type Player = z.infer<typeof playerSchema>;

// Game State Schema
export const gameStateSchema = z.object({
  room_id: z.string(),
  phase: z.enum(["waiting", "playing", "ended"]),
  act: z.number().int().min(1),
  players: z.array(playerSchema),
  current_event: z.any().optional(),
  clues_unlocked: z.array(z.string())
});
export type GameState = z.infer<typeof gameStateSchema>;

// Phase Unlock Schema
export const phaseUnlockSchema = z.object({
  new_act: z.number().int().min(1),
  distributed_role_cards: z.array(roleCardSchema).optional(),
  distributed_clues: z.array(clueSchema).optional()
});
export type PhaseUnlock = z.infer<typeof phaseUnlockSchema>;

// Export all schemas for easy import
export const wsSchemas = {
  chatMessage: chatMessageSchema,
  clue: clueSchema,
  roleCard: roleCardSchema,
  player: playerSchema,
  gameState: gameStateSchema,
  phaseUnlock: phaseUnlockSchema
};

export default wsSchemas;
```

- [ ] **Step 2: Create Python package init file**

```python
# shared/schemas/__init__.py
# Python shared schemas package
# Zod schemas are in ws.ts (TypeScript)
# Pydantic models are in server/models/ws.py
```

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd client && npx tsc --noEmit`
Expected: No errors related to shared/schemas

- [ ] **Step 4: Commit**

```bash
git add shared/schemas/ws.ts shared/schemas/__init__.py
git commit -m "feat: add shared Zod schemas for WebSocket messages"
```

---

## Task 2: 创建 Pydantic v2 模型

**Files:**
- Create: `server/models/ws.py`
- Modify: `server/models.py:1-50` (add deprecation notice)

- [ ] **Step 1: Write Pydantic models matching Zod schemas**

```python
# server/models/ws.py
"""
WebSocket message models - Pydantic v2

These models mirror the Zod schemas in shared/schemas/ws.ts
Keep field names and types consistent between both files.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ChatPhase(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    ENDED = "ended"


class CluePhase(str, Enum):
    ACT1 = "act1"
    ACT2 = "act2"


class ClueType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class ChatMessage(BaseModel):
    """Chat message model - mirrors Zod chatMessageSchema"""
    message_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    player_id: str
    role_name: str
    timestamp: str  # ISO 8601 format
    from_player_name: str


class Clue(BaseModel):
    """Clue model - mirrors Zod clueSchema"""
    id: str
    title: str
    content: str
    unlock_phase: CluePhase
    clue_type: ClueType
    related_role_id: Optional[str] = None


class RoleCard(BaseModel):
    """Role card model - mirrors Zod roleCardSchema"""
    role_id: str
    role_name: str
    player_id: str
    layer: int = Field(..., ge=1, le=3)
    content: str
    secrets: Optional[List[str]] = None


class Player(BaseModel):
    """Player model - mirrors Zod playerSchema"""
    player_id: str
    role_id: str
    role_name: str
    is_admin: bool


class GameState(BaseModel):
    """Game state model - mirrors Zod gameStateSchema"""
    room_id: str
    phase: ChatPhase
    act: int = Field(..., ge=1)
    players: List[Player]
    current_event: Optional[dict] = None
    clues_unlocked: List[str] = []


class PhaseUnlock(BaseModel):
    """Phase unlock response - mirrors Zod phaseUnlockSchema"""
    new_act: int = Field(..., ge=1)
    distributed_role_cards: Optional[List[RoleCard]] = None
    distributed_clues: Optional[List[Clue]] = None


__all__ = [
    "ChatMessage",
    "Clue",
    "RoleCard",
    "Player",
    "GameState",
    "PhaseUnlock",
    "ChatPhase",
    "CluePhase",
    "ClueType"
]
```

- [ ] **Step 2: Add deprecation notice to old models.py**

```python
# server/models.py (add at top, after imports)
"""
DEPRECATION NOTICE:

This file contains legacy Pydantic models. New WebSocket message models
should use server/models/ws.py which mirrors the Zod schemas in
shared/schemas/ws.ts for type consistency across the stack.

Migration plan:
- Phase 1: Add new models to ws.py (DONE)
- Phase 2: Gradually migrate API routes to use ws.py models
- Phase 3: Remove this file after all routes migrated
"""
```

- [ ] **Step 3: Test Pydantic models**

Run: `python -c "from server.models.ws import ChatMessage; m = ChatMessage(message_id='1', content='test', player_id='p1', role_name='Role', timestamp='2026-05-11T12:00:00Z', from_player_name='Player'); print(m)"`
Expected: ChatMessage object printed successfully

- [ ] **Step 4: Commit**

```bash
git add server/models/ws.py server/models.py
git commit -m "feat: add Pydantic v2 models matching Zod schemas"
```

---

## Task 3: 创建前端验证工具

**Files:**
- Create: `client/src/utils/schema-validation.ts`

- [ ] **Step 1: Write validation utility functions**

```typescript
// client/src/utils/schema-validation.ts
import { wsSchemas, type ChatMessage, type Clue, type RoleCard } from "@shared/schemas/ws";

/**
 * Validation result type
 */
export interface ValidationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Validate chat message from server or WebSocket
 */
export function validateChatMessage(raw: unknown): ValidationResult<ChatMessage> {
  const result = wsSchemas.chatMessage.safeParse(raw);
  
  if (!result.success) {
    return {
      success: false,
      error: `Invalid chat message: ${result.error.message}`
    };
  }
  
  return { success: true, data: result.data };
}

/**
 * Validate clue from server or WebSocket
 */
export function validateClue(raw: unknown): ValidationResult<Clue> {
  const result = wsSchemas.clue.safeParse(raw);
  
  if (!result.success) {
    return {
      success: false,
      error: `Invalid clue: ${result.error.message}`
    };
  }
  
  return { success: true, data: result.data };
}

/**
 * Validate role card from server or WebSocket
 */
export function validateRoleCard(raw: unknown): ValidationResult<RoleCard> {
  const result = wsSchemas.roleCard.safeParse(raw);
  
  if (!result.success) {
    return {
      success: false,
      error: `Invalid role card: ${result.error.message}`
    };
  }
  
  return { success: true, data: result.data };
}

/**
 * Batch validate multiple items (efficient for arrays)
 */
export function validateBatch<T>(
  items: unknown[],
  validator: (item: unknown) => ValidationResult<T>
): { valid: T[]; invalid: { item: unknown; error: string }[] } {
  const valid: T[] = [];
  const invalid: { item: unknown; error: string }[] = [];
  
  for (const item of items) {
    const result = validator(item);
    if (result.success && result.data) {
      valid.push(result.data);
    } else {
      invalid.push({ item, error: result.error || "Unknown error" });
    }
  }
  
  return { valid, invalid };
}

/**
 * Log validation errors for debugging (dev only)
 */
export function logValidationError(context: string, error: string): void {
  if (import.meta.env.DEV) {
    console.error(`[${context}] Validation error:`, error);
  }
}
```

- [ ] **Step 2: Update TypeScript path aliases**

Check `client/tsconfig.json` has:
```json
{
  "compilerOptions": {
    "paths": {
      "@shared/*": ["../shared/*"]
    }
  }
}
```

If missing, add the path alias.

- [ ] **Step 3: Test validation utilities**

Create test file `client/tests/unit/schema-validation.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { validateChatMessage, validateClue } from '@/utils/schema-validation';

describe('schema-validation', () => {
  it('validates correct chat message', () => {
    const result = validateChatMessage({
      message_id: '1',
      content: 'Hello',
      player_id: 'p1',
      role_name: 'Detective',
      timestamp: '2026-05-11T12:00:00Z',
      from_player_name: 'Alice'
    });
    
    expect(result.success).toBe(true);
    expect(result.data?.content).toBe('Hello');
  });
  
  it('rejects invalid chat message', () => {
    const result = validateChatMessage({
      message_id: '1',
      content: '', // Empty content should fail min_length
      player_id: 'p1',
      role_name: 'Detective',
      timestamp: '2026-05-11T12:00:00Z',
      from_player_name: 'Alice'
    });
    
    expect(result.success).toBe(false);
    expect(result.error).toContain('minLength');
  });
  
  it('validates correct clue', () => {
    const result = validateClue({
      id: 'clue1',
      title: 'Secret Letter',
      content: 'The will was forged',
      unlock_phase: 'act1',
      clue_type: 'public'
    });
    
    expect(result.success).toBe(true);
    expect(result.data?.title).toBe('Secret Letter');
  });
});
```

- [ ] **Step 4: Run tests**

Run: `cd client && npm test -- schema-validation.test.ts`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add client/src/utils/schema-validation.ts client/tests/unit/schema-validation.test.ts
git commit -m "feat: add schema validation utilities for frontend"
```

---

## Task 4: 集成 Store 验证

**Files:**
- Modify: `client/src/stores/game.ts`

- [ ] **Step 1: Import and integrate validation**

Find `client/src/stores/game.ts` and update message handling functions:

```typescript
// Add imports at top
import { 
  validateChatMessage, 
  validateClue, 
  validateRoleCard 
} from '@/utils/schema-validation';
import type { ChatMessage, Clue, RoleCard } from '@shared/schemas/ws';

// Update addMessage function
const addMessage = (raw: unknown) => {
  const result = validateChatMessage(raw);
  
  if (!result.success) {
    console.error("Failed to validate message:", result.error);
    return; // Skip invalid messages
  }
  
  state.messages.push(result.data);
  
  // Deduplication
  const key = `${result.data.message_id}-${result.data.player_id}`;
  if (state.seenMessageKeys.has(key)) return;
  state.seenMessageKeys.add(key);
};

// Update handleClueUnlock function
const handleClueUnlock = (raw: unknown) => {
  const result = validateClue(raw);
  
  if (!result.success) {
    console.error("Failed to validate clue:", result.error);
    return;
  }
  
  // Check for duplicates
  if (state.clues.some(c => c.id === result.data.id)) return;
  
  state.clues.push(result.data);
  state.clues_unlocked.push(result.data.id);
};

// Update receiveRoleCard function
const receiveRoleCard = (raw: unknown) => {
  const result = validateRoleCard(raw);
  
  if (!result.success) {
    console.error("Failed to validate role card:", result.error);
    return;
  }
  
  // Check for duplicates
  if (state.distributed_role_cards.has(result.data.role_id)) return;
  
  state.distributed_role_cards.add(result.data.role_id);
  state.roleCards.push(result.data);
};
```

- [ ] **Step 2: Test store integration**

Run: `cd client && npm test -- stores/game.test.ts` (or create test if missing)

Expected: Store functions handle validated data correctly

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd client && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add client/src/stores/game.ts
git commit -m "feat: integrate schema validation into game store"
```

---

## Task 5: 更新 API 端点使用 Pydantic

**Files:**
- Modify: `server/api/chat.get.ts` (or equivalent chat route)
- Modify: `server/api/clue.get.ts` (or equivalent clue route)

- [ ] **Step 1: Update chat endpoint**

Find chat API endpoint and add response model:

```python
# server/api/chat.py (example)
from fastapi import APIRouter
from server.models.ws import ChatMessage

router = APIRouter()

@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessage])
async def get_messages(room_id: str):
    """Get chat messages for a room with validation"""
    messages = await game_manager.get_messages(room_id)
    
    # Validate each message using Pydantic
    validated_messages = []
    for msg in messages:
        try:
            validated = ChatMessage.model_validate(msg)
            validated_messages.append(validated)
        except Exception as e:
            logger.warning(f"Invalid message in room {room_id}: {e}")
            continue
    
    return validated_messages
```

- [ ] **Step 2: Update clue endpoint**

```python
# server/api/clue.py (example)
from fastapi import APIRouter
from server.models.ws import Clue

router = APIRouter()

@router.get("/rooms/{room_id}/clues", response_model=list[Clue])
async def get_clues(room_id: str):
    """Get unlocked clues for a room with validation"""
    clues = await game_manager.get_clues(room_id)
    
    # Validate each clue
    validated_clues = []
    for clue in clues:
        try:
            validated = Clue.model_validate(clue)
            validated_clues.append(validated)
        except Exception as e:
            logger.warning(f"Invalid clue in room {room_id}: {e}")
            continue
    
    return validated_clues
```

- [ ] **Step 3: Test API endpoints**

Run: `pytest tests/test_api_chat.py tests/test_api_clue.py -v`
Expected: All tests pass with validated responses

- [ ] **Step 4: Commit**

```bash
git add server/api/chat.py server/api/clue.py
git commit -m "feat: use Pydantic models for API response validation"
```

---

## Task 6: 添加 Schema 单元测试

**Files:**
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Write comprehensive schema tests**

```python
# tests/test_schemas.py
import pytest
from server.models.ws import (
    ChatMessage, Clue, RoleCard, Player, 
    GameState, PhaseUnlock, CluePhase, ClueType
)


class TestChatMessage:
    def test_valid_chat_message(self):
        msg = ChatMessage(
            message_id="1",
            content="Hello",
            player_id="p1",
            role_name="Detective",
            timestamp="2026-05-11T12:00:00Z",
            from_player_name="Alice"
        )
        assert msg.content == "Hello"
        assert msg.player_id == "p1"
    
    def test_rejects_empty_content(self):
        with pytest.raises(ValueError):
            ChatMessage(
                message_id="1",
                content="",  # Empty - violates min_length
                player_id="p1",
                role_name="Detective",
                timestamp="2026-05-11T12:00:00Z",
                from_player_name="Alice"
            )
    
    def test_rejects_long_content(self):
        with pytest.raises(ValueError):
            ChatMessage(
                message_id="1",
                content="x" * 2001,  # Too long - violates max_length
                player_id="p1",
                role_name="Detective",
                timestamp="2026-05-11T12:00:00Z",
                from_player_name="Alice"
            )


class TestClue:
    def test_valid_clue_public(self):
        clue = Clue(
            id="clue1",
            title="Secret Letter",
            content="The will was forged",
            unlock_phase=CluePhase.ACT1,
            clue_type=ClueType.PUBLIC
        )
        assert clue.unlock_phase == CluePhase.ACT1
    
    def test_valid_clue_private(self):
        clue = Clue(
            id="clue2",
            title="Private Diary",
            content="I killed him",
            unlock_phase=CluePhase.ACT2,
            clue_type=ClueType.PRIVATE
        )
        assert clue.clue_type == ClueType.PRIVATE
    
    def test_optional_related_role(self):
        clue = Clue(
            id="clue3",
            title="No Connection",
            content="Random info",
            unlock_phase=CluePhase.ACT1,
            clue_type=ClueType.PUBLIC,
            related_role_id=None  # Optional field
        )
        assert clue.related_role_id is None


class TestRoleCard:
    def test_valid_role_card_layer_1(self):
        card = RoleCard(
            role_id="r1",
            role_name="Detective",
            player_id="p1",
            layer=1,
            content="You are the detective"
        )
        assert card.layer == 1
    
    def test_rejects_invalid_layer(self):
        with pytest.raises(ValueError):
            RoleCard(
                role_id="r1",
                role_name="Detective",
                player_id="p1",
                layer=5,  # Invalid - must be 1-3
                content="You are the detective"
            )


class TestGameState:
    def test_valid_game_state(self):
        state = GameState(
            room_id="room1",
            phase="playing",
            act=1,
            players=[],
            clues_unlocked=[]
        )
        assert state.phase == "playing"
        assert state.act == 1


class TestPhaseUnlock:
    def test_phase_unlock_with_clues(self):
        unlock = PhaseUnlock(
            new_act=2,
            distributed_clues=[
                Clue(
                    id="clue1",
                    title="Test",
                    content="Content",
                    unlock_phase=CluePhase.ACT2,
                    clue_type=ClueType.PUBLIC
                )
            ]
        )
        assert unlock.new_act == 2
        assert len(unlock.distributed_clues) == 1
```

- [ ] **Step 2: Run schema tests**

Run: `pytest tests/test_schemas.py -v`
Expected: All tests pass (8+ tests)

- [ ] **Step 3: Check coverage**

Run: `pytest tests/test_schemas.py --cov=server.models.ws --cov-report=term-missing`
Expected: High coverage of ws.py models

- [ ] **Step 4: Commit**

```bash
git add tests/test_schemas.py
git commit -m "test: add comprehensive schema validation tests"
```

---

## Task 7: 验证整体验收标准

**Files:**
- No changes - verification only

- [ ] **Step 1: Verify TypeScript compilation**

Run: `cd client && npx tsc --noEmit`
Expected: Exit code 0, no errors

- [ ] **Step 2: Verify shared schemas count**

Check: `shared/schemas/ws.ts` exports at least 3 core schemas (chatMessage, clue, roleCard)
Expected: 6 schemas exported (chatMessage, clue, roleCard, player, gameState, phaseUnlock)

- [ ] **Step 3: Verify deprecation notice**

Check: `shared/ws_types.py` has deprecation comment or file is marked for removal
Expected: Deprecation notice present

- [ ] **Step 4: Verify test count**

Run: `pytest tests/test_schemas.py -v --collect-only`
Expected: 8+ test functions collected

- [ ] **Step 5: Final commit**

```bash
git status
# Review all changes
git commit -am "chore: complete phase 1 - core type unification"
```

---

## Phase 1 Completion Checklist

- [ ] `npx tsc --noEmit` exits with code 0 in client/
- [ ] At least 3 core schemas shared (chat, clue, role) - actually 6 implemented
- [ ] shared/ws_types.py marked as deprecated
- [ ] Schema unit tests added (8+ tests)
- [ ] All tests pass: `pytest tests/test_schemas.py` and `cd client && npm test`
- [ ] Git commits made for each task

---

## Next Steps

After Phase 1 completes, proceed to:
- **Phase 2:** 关键组件清理 (delete unused components, implement store actions)
- **Phase 3:** 用户体验优化 (animations, deduplication, loading states)

Plan saved to: `docs/superpowers/plans/2026-05-11-phase1-type-unification.md`
