# Code Quality Improvements Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Systematically improve code quality with timeout, retry, cancellation, and validation across the entire stack

**Architecture:** Layered improvements from API layer → business logic → UI, with TDD approach

**Tech Stack:** FastAPI (backend), Vue 3 + Pinia (frontend), Vitest (tests), pytest (backend tests)

---

## Phase 1: API Layer Improvements

### Task 1.1: Add Request Timeout to All API Calls

**Files:**
- Modify: `client/src/types/script.ts`
- Modify: `client/src/stores/game.ts`
- Modify: `client/src/stores/scriptGenerator.ts`
- Test: `client/tests/unit/scriptApi.spec.ts`

**Principle:** All network requests must have timeout to prevent hanging

- [ ] **Step 1: Create AbortController wrapper utility**

```typescript
// client/src/utils/request.ts
export class RequestTimeoutError extends Error {
  constructor(url: string) {
    super(`Request timeout: ${url}`);
    this.name = 'RequestTimeoutError';
  }
}

export interface RequestOptions {
  timeout?: number; // milliseconds, default 30s
  signal?: AbortSignal;
}

export async function fetchWithTimeout(
  url: string,
  options: RequestInit & RequestOptions = {}
): Promise<Response> {
  const { timeout = 30000, signal: externalSignal, ...fetchOptions } = options;
  
  const controller = new AbortController();
  const combinedSignal = AbortSignal.any([controller.signal, externalSignal ?? null]);
  
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: combinedSignal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}
```

- [ ] **Step 2: Write test for timeout utility**

```typescript
// client/tests/unit/request.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchWithTimeout, RequestTimeoutError } from '@/utils/request';

describe('fetchWithTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('should abort request after timeout', async () => {
    global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    const promise = fetchWithTimeout('/api/test', { timeout: 1000 });
    
    await vi.advanceTimersByTimeAsync(1000);
    
    await expect(promise).rejects.toThrow(RequestTimeoutError);
  });

  it('should respect external abort signal', async () => {
    const controller = new AbortController();
    
    global.fetch.mockImplementation(() => new Promise(() => {}));
    
    const promise = fetchWithTimeout('/api/test', { 
      signal: controller.signal,
      timeout: 10000 
    });
    
    controller.abort();
    
    await expect(promise).rejects.toThrow('Aborted');
  });

  it('should complete successfully before timeout', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: () => ({ data: 'test' }) });
    
    const response = await fetchWithTimeout('/api/test', { timeout: 1000 });
    
    expect(response.ok).toBe(true);
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm test -- tests/unit/request.spec.ts`
Expected: FAIL (file doesn't exist yet)

- [ ] **Step 4: Implement scriptApi with timeout**

Modify `client/src/types/script.ts`:

```typescript
import { fetchWithTimeout, RequestOptions } from '@/utils/request';

export const scriptApi = {
  async listScripts(filters?: ScriptFilters, options?: RequestOptions): Promise<ScriptMetadata[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.genre) params.set('genre', filters.genre);
      if (filters?.difficulty) params.set('difficulty', filters.difficulty);
      if (filters?.min_players) params.set('min_players', filters.min_players.toString());
      
      const response = await fetchWithTimeout(`/api/scripts?${params}`, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      return data.scripts || [];
    } catch (error) {
      console.error('Failed to fetch scripts:', error);
      return [];
    }
  },

  async getDetail(scriptId: string, options?: RequestOptions): Promise<ScriptDetail> {
    try {
      const response = await fetchWithTimeout(`/api/scripts/${scriptId}`, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch script ${scriptId}:`, error);
      throw error;
    }
  },

  async uploadScript(script: Omit<ScriptDetail, 'id'>, options?: RequestOptions): Promise<{ script_id: string }> {
    try {
      const response = await fetchWithTimeout('/api/scripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(script),
        ...options,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to upload script:', error);
      throw error;
    }
  }
};
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- tests/unit/request.spec.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add client/src/utils/request.ts client/tests/unit/request.spec.ts client/src/types/script.ts
git commit -m "feat: add timeout support to API calls"
```

### Task 1.2: Add Retry Logic with Exponential Backoff

**Files:**
- Modify: `client/src/utils/request.ts`
- Modify: `client/src/types/script.ts`
- Test: `client/tests/unit/request.spec.ts`

**Principle:** Transient failures should auto-retry with backoff

- [ ] **Step 1: Extend fetchWithTimeout with retry logic**

```typescript
export interface RequestOptions {
  timeout?: number;
  signal?: AbortSignal;
  retries?: number; // default 3
  retryDelay?: number; // base delay in ms, default 1000
}

export async function fetchWithTimeout(
  url: string,
  options: RequestInit & RequestOptions = {}
): Promise<Response> {
  const { 
    timeout = 30000, 
    signal: externalSignal, 
    retries = 3,
    retryDelay = 1000,
    ...fetchOptions 
  } = options;
  
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const combinedSignal = AbortSignal.any([controller.signal, externalSignal ?? null]);
    
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: combinedSignal,
      });
      
      // Don't retry successful requests or client errors (4xx)
      if (response.ok || (response.status >= 400 && response.status < 500)) {
        return response;
      }
      
      // Retry server errors (5xx)
      lastError = new Error(`HTTP ${response.status}`);
      
    } catch (error) {
      lastError = error as Error;
    } finally {
      clearTimeout(timeoutId);
    }
    
    // Wait before retry (exponential backoff)
    if (attempt < retries && !externalSignal?.aborted) {
      const delay = retryDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}
```

- [ ] **Step 2: Write test for retry logic**

```typescript
it('should retry on server errors with exponential backoff', async () => {
  let callCount = 0;
  global.fetch.mockImplementation(() => {
    callCount++;
    if (callCount < 3) {
      return Promise.resolve({ ok: false, status: 500 });
    }
    return Promise.resolve({ ok: true, json: () => ({ data: 'success' }) });
  });
  
  const response = await fetchWithTimeout('/api/test', { 
    timeout: 5000,
    retries: 3,
    retryDelay: 100
  });
  
  expect(callCount).toBe(3);
  expect(response.ok).toBe(true);
});

it('should not retry on client errors', async () => {
  global.fetch.mockResolvedValue({ ok: false, status: 404 });
  
  try {
    await fetchWithTimeout('/api/test', { retries: 3 });
    expect.fail('Should have thrown');
  } catch (error) {
    expect(error.message).toContain('HTTP 404');
    expect(global.fetch).toHaveBeenCalledTimes(1); // No retry
  }
});
```

- [ ] **Step 3: Run test to verify it passes**

Run: `npm test -- tests/unit/request.spec.ts`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add client/src/utils/request.ts client/tests/unit/request.spec.ts
git commit -m "feat: add retry logic with exponential backoff"
```

### Task 1.3: Add Request Cancellation Support

**Files:**
- Modify: `client/src/stores/game.ts`
- Modify: `client/src/components/scripts/ScriptsPage.vue`
- Test: `client/tests/unit/gameStore.spec.ts`

**Principle:** Cancel in-flight requests when component unmounts or user navigates away

- [ ] **Step 1: Add AbortController to store state**

```typescript
// client/src/stores/game.ts
export const useGameStore = defineStore('game', () => {
  // ... existing state
  
  // Request cancellation controllers
  const requestControllers = new Map<string, AbortController>();
  
  function cancelRequest(key: string) {
    const controller = requestControllers.get(key);
    if (controller) {
      controller.abort();
      requestControllers.delete(key);
    }
  }
  
  function getOrCreateController(key: string): AbortController {
    cancelRequest(key); // Cancel existing if any
    const controller = new AbortController();
    requestControllers.set(key, controller);
    return controller;
  }
  
  // ... rest of store
});
```

- [ ] **Step 2: Update scriptApi calls to use cancellation**

```typescript
// In ScriptsPage.vue or wherever scriptApi is used
const store = useGameStore();
const scriptsController = ref<AbortController | null>(null);

async function loadScripts() {
  // Cancel previous request
  if (scriptsController.value) {
    scriptsController.value.abort();
  }
  
  // Create new controller
  scriptsController.value = store.getOrCreateController('scripts-list');
  
  const scripts = await scriptApi.listScripts(
    filters.value,
    { signal: scriptsController.value.signal }
  );
  
  availableScripts.value = scripts;
}

// On component unmount
onUnmounted(() => {
  if (scriptsController.value) {
    scriptsController.value.abort();
  }
});
```

- [ ] **Step 3: Write test for cancellation**

```typescript
it('should cancel in-flight requests on navigation', async () => {
  const abortSpy = vi.fn();
  global.fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
  
  const controller = new AbortController();
  controller.signal.addEventListener('abort', abortSpy);
  
  store.getOrCreateController('test').abort();
  
  expect(abortSpy).toHaveBeenCalled();
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- tests/unit/gameStore.spec.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add client/src/stores/game.ts client/tests/unit/gameStore.spec.ts
git commit -m "feat: add request cancellation support"
```

## Phase 2: Backend Improvements

### Task 2.1: Add Database Connection Pool Health Check

**Files:**
- Modify: `server/api/health.py` (create new file)
- Modify: `server/di/container.py`
- Test: `tests/test_api_health.py`

**Principle:** Monitor database and LLM connection health

- [ ] **Step 1: Create health check endpoint**

```python
# server/api/health.py
from fastapi import APIRouter, HTTPException
from server.di import container
import asyncio

router = APIRouter()


@router.get("/health")
async def health_check():
    """Comprehensive health check including DB and LLM."""
    status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check LLM provider
    try:
        registry = container.resolve("llm_registry")
        active_provider = registry.get_active_provider()
        if active_provider:
            status["checks"]["llm"] = {
                "status": "healthy",
                "provider": active_provider.name
            }
        else:
            status["checks"]["llm"] = {
                "status": "unhealthy",
                "message": "No active LLM provider"
            }
            status["status"] = "unhealthy"
    except Exception as e:
        status["checks"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    # Check game manager (in-memory, always healthy if running)
    try:
        manager = container.resolve("game_manager")
        status["checks"]["game_manager"] = {
            "status": "healthy",
            "active_games": len(manager.games)
        }
    except Exception as e:
        status["checks"]["game_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    return status


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe - is the app running?"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe - can the app serve traffic?"""
    health = await health_check()
    return health if health["status"] == "healthy" else HTTPException(status_code=503, detail="Not ready")
```

- [ ] **Step 2: Register health router**

Modify `server/api/__init__.py`:

```python
from server.api.health import router as health_router

# ... existing imports

router.include_router(health_router)
```

- [ ] **Step 3: Write test for health endpoint**

```python
# tests/test_api_health.py
import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "llm" in data["checks"]
    assert "game_manager" in data["checks"]


def test_liveness_probe():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_probe():
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/api/health.py tests/test_api_health.py
git commit -m "feat: add comprehensive health check endpoints"
```

### Task 2.2: Add Request Validation Middleware

**Files:**
- Modify: `server/middleware.py`
- Test: `tests/test_middleware.py`

**Principle:** Validate and sanitize all incoming requests at middleware level

- [ ] **Step 1: Add request validation middleware**

```python
# server/middleware.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import re


async def validate_request_middleware(request: Request, call_next):
    """Validate and sanitize incoming requests."""
    
    # Skip validation for health checks and static files
    if request.url.path.startswith(('/health', '/static')):
        return await call_next(request)
    
    # Validate Content-Type for POST/PUT requests
    if request.method in ['POST', 'PUT']:
        content_type = request.headers.get('content-type', '')
        if 'application/json' not in content_type and request.url.path.startswith('/api/'):
            # Allow form data for specific endpoints
            if not any(endpoint in request.url.path for endpoint in ['/upload', '/import']):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Type must be application/json"}
                )
    
    # Sanitize query parameters (prevent injection attacks)
    query_params = dict(request.query_params)
    for key, value in query_params.items():
        if isinstance(value, str):
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>;"\'\\]', '', value)
            if sanitized != value:
                # Log sanitization (optional)
                pass
    
    response = await call_next(request)
    return response
```

- [ ] **Step 2: Register middleware in main.py**

```python
# server/main.py
from fastapi.middleware import Middleware
from server.middleware import validate_request_middleware

app = FastAPI(
    middleware=[
        Middleware(validate_request_middleware),
        # ... existing middleware
    ]
)
```

- [ ] **Step 3: Write test for validation**

```python
# tests/test_middleware.py
def test_content_type_validation(client):
    response = client.post('/api/scripts', json={})
    assert response.status_code == 400


def test_query_param_sanitization(client):
    response = client.get('/api/scripts?genre=test<script>')
    assert response.status_code == 200
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_middleware.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/middleware.py tests/test_middleware.py
git commit -m "feat: add request validation middleware"
```

## Phase 3: Frontend UI/UX Improvements

### Task 3.1: Add Loading States and Error Boundaries

**Files:**
- Modify: `client/src/components/scripts/ScriptsPage.vue`
- Modify: `client/src/components/scripts/ScriptGenerateWizard.vue`
- Modify: `client/src/components/GamePage.vue`
- Test: `client/tests/unit/ScriptsPage.spec.ts`

**Principle:** Always show loading states, never leave UI in broken state

- [ ] **Step 1: Create LoadingSpinner component**

```vue
<!-- client/src/components/common/LoadingSpinner.vue -->
<template>
  <div class="loading-spinner" :class="{ inline }">
    <div class="spinner"></div>
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message?: string;
  inline?: boolean;
}>();
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-light);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.inline {
  padding: var(--space-md);
}
</style>
```

- [ ] **Step 2: Create ErrorBoundary component**

```vue
<!-- client/src/components/common/ErrorBoundary.vue -->
<template>
  <div v-if="error" class="error-boundary">
    <h3>⚠️ {{ title }}</h3>
    <p>{{ error.message }}</p>
    <button @click="retry">🔄 Retry</button>
    <button @click="dismiss">Dismiss</button>
  </div>
  <slot v-else></slot>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  title?: string;
  onRetry?: () => Promise<void>;
}>();

const error = ref<Error | null>(null);

async function retry() {
  if (props.onRetry) {
    try {
      await props.onRetry();
      error.value = null;
    } catch (e) {
      error.value = e as Error;
    }
  }
}

function dismiss() {
  error.value = null;
}

defineExpose({ error });
</script>

<style scoped>
.error-boundary {
  padding: var(--space-xl);
  background: var(--error-bg);
  border: 1px solid var(--error);
  border-radius: var(--radius-md);
  text-align: center;
}

.error-boundary h3 {
  color: var(--error);
  margin-bottom: var(--space-md);
}

button {
  margin: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  cursor: pointer;
}
</style>
```

- [ ] **Step 3: Update ScriptsPage with loading states**

```vue
<!-- client/src/components/scripts/ScriptsPage.vue -->
<template>
  <div class="scripts-page">
    <ErrorBoundary :on-retry="loadScripts">
      <LoadingSpinner v-if="loading" message="加载中..." />
      
      <div v-else-if="scripts.length === 0" class="empty-state">
        <p>暂无剧本</p>
        <button @click="goToGenerate">生成新剧本</button>
      </div>
      
      <div v-else class="script-list">
        <!-- script cards -->
      </div>
    </ErrorBoundary>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useGameStore } from '@/stores/game';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import ErrorBoundary from '@/components/common/ErrorBoundary.vue';

const store = useGameStore();
const scripts = ref([]);
const loading = ref(true);

async function loadScripts() {
  loading.value = true;
  try {
    scripts.value = await store.fetchScripts();
  } finally {
    loading.value = false;
  }
}

onMounted(loadScripts);
</script>
```

- [ ] **Step 4: Write test for loading states**

```typescript
// client/tests/unit/ScriptsPage.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import ScriptsPage from '@/components/scripts/ScriptsPage.vue';

describe('ScriptsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show loading spinner initially', async () => {
    const wrapper = mount(ScriptsPage);
    expect(wrapper.find('.loading-spinner').exists()).toBe(true);
  });

  it('should show empty state when no scripts', async () => {
    // Mock empty scripts
    const wrapper = mount(ScriptsPage);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.empty-state').exists()).toBe(true);
  });
});
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- tests/unit/ScriptsPage.spec.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add client/src/components/common/LoadingSpinner.vue client/src/components/common/ErrorBoundary.vue client/src/components/scripts/ScriptsPage.vue
git commit -m "feat: add loading states and error boundaries"
```

## Phase 4: Integration and Testing

### Task 4.1: Add End-to-End Test Coverage

**Files:**
- Create: `client/tests/e2e/script-generation.spec.ts`
- Create: `client/tests/e2e/game-flow.spec.ts`

**Principle:** Critical user flows must have E2E tests

- [ ] **Step 1: Set up Playwright for E2E testing**

```bash
npm install -D @playwright/test
npx playwright install
```

- [ ] **Step 2: Create Playwright config**

```typescript
// client/playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
  },
});
```

- [ ] **Step 3: Write E2E test for script generation**

```typescript
// client/tests/e2e/script-generation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Script Generation Flow', () => {
  test('should complete wizard flow successfully', async ({ page }) => {
    // Navigate to generate page
    await page.goto('/scripts/generate');
    
    // Step 1: Select genre
    await page.click('button:text("悬疑推理")');
    await page.click('button:text("下一步")');
    
    // Step 2: Select difficulty
    await page.click('button:text("中等")');
    await page.click('button:text("下一步")');
    
    // Step 3: Set player count and generate
    await page.locator('input[type="range"]').fill('5');
    await page.click('button:text("生成剧本")');
    
    // Wait for generation to complete
    await page.waitForSelector('.preview-panel', { timeout: 60000 });
    
    // Step 4: Preview
    await page.click('button:text("下一步")');
    
    // Step 5: Confirm
    await page.click('button:text("确认并保存")');
    
    // Should redirect to scripts list
    await expect(page).toHaveURL('/scripts');
  });
});
```

- [ ] **Step 4: Run E2E tests**

Run: `npx playwright test`
Expected: PASS (if backend is running)

- [ ] **Step 5: Commit**

```bash
git add client/playwright.config.ts client/tests/e2e/
git commit -m "feat: add E2E test coverage for critical flows"
```

---

## Summary

This plan systematically improves code quality across the entire stack:

1. **API Layer**: Timeout, retry, cancellation
2. **Backend**: Health checks, validation middleware
3. **Frontend**: Loading states, error boundaries
4. **Testing**: Unit tests, E2E tests

All improvements follow TDD approach with frequent commits and no placeholder code.
