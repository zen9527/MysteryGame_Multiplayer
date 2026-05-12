# Superpowers Documentation

This directory contains architectural design decisions and implementation plans for the Script Murder (剧本杀) game.

## Structure

```
superpowers/
├── README.md              # This file
├── plans/                 # Implementation plans (temporary, deleted after completion)
└── specs/                 # Design specifications (permanent ADRs)
```

## Permanent Design Records (specs/)

These documents capture core architectural decisions and should be retained:

### Core Architecture Designs

| Document | Purpose | Status |
|----------|---------|--------|
| [info-isolation-design.md](specs/2026-04-26-info-isolation-design.md) | Player information isolation, role card layers, private messaging, clue distribution | ✅ Implemented |
| [script-persistence-design.md](specs/2026-05-10-script-persistence-design.md) | SQLite-based script storage, API endpoints, masking strategy | ✅ Implemented |
| [modular-refactor-design.md](specs/2026-05-11-modular-refactor-design.md) | LLM Provider, Script Engine, Game Engine modular architecture | ✅ Implemented |

## Implementation Plans (plans/)

Implementation plans are **temporary documents** used to guide development. They are deleted after successful implementation to keep the documentation clean.

### Plan Lifecycle

1. **Created**: When a new feature or refactoring is planned
2. **Implemented**: Task-by-task execution with verification
3. **Deleted**: After completion and commit

### Why Delete Plans?

- Plans contain implementation details that become obsolete
- Code itself is the source of truth for implemented features
- Keeping only design specs reduces noise and maintenance burden
- Future developers can read code + design specs to understand decisions

## Key Architectural Decisions

### Info Isolation (2026-04-26)

**Problem**: Players should only see their own role cards, private messages, and assigned clues.

**Decision**: 
- Three-layer role card system (layer 1→2→3 progressive unlock)
- Per-player clue distribution with `target_player_ids` and `unlock_phase`
- DM→player private messaging via WebSocket
- Distribution cache for WS reconnect resilience

**Impact**: `GameState` extended with `distributed_role_cards`, `distributed_clues`, `distributed_dm_private`

### Script Persistence (2026-05-10)

**Problem**: Generated scripts are lost on server restart; no way to reuse good scripts.

**Decision**:
- SQLite storage with `ScriptRepository` (data access) + `ScriptService` (business logic)
- Full JSON storage in `full_content` field for easy export/import
- Frontend masks sensitive fields (`true_killer`, `clues`) in preview
- REST API for browsing, uploading, deleting scripts

**Impact**: New `/api/scripts` endpoints, `script_id` parameter in room creation

### Modular Refactor (2026-05-11)

**Problem**: Monolithic `LLMClient` and `HostDM` make it hard to add new LLM providers and autonomous DM features.

**Decision**:
- **LLM Provider Layer**: Abstract `LLMProvider` with concrete implementations (OpenAI, Anthropic, Gemini)
- **Script Engine**: Dedicated `ScriptGenerator` with genre templates and JSON normalization
- **Game Engine**: `GameHost` + `GameScheduler` for autonomous DM interventions

**Impact**: `server/llm/`, `server/script_engine/`, `server/game_engine/` packages; DI container updated

## Documentation Principles

1. **Design specs are permanent**: They capture WHY decisions were made
2. **Plans are temporary**: They capture HOW to implement (code is the truth)
3. **One spec per major decision**: Avoid fragmentation
4. **Link spec to implementation**: Reference commit hashes or PR numbers
5. **Keep it concise**: 1-3 pages per spec, focus on decisions not details

## Maintenance

- **Weekly**: Review completed plans, delete if implementation verified
- **Monthly**: Review specs for outdated information
- **On major refactor**: Create new spec, deprecate old one
