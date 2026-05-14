// Note: This file is optional and currently disabled due to missing shared schemas
// import { wsSchemas, type ChatMessage, type Clue, type RoleCard } from "@shared/schemas/ws";

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
export function validateChatMessage(raw: unknown): ValidationResult<Record<string, unknown>> {
  // Placeholder - actual implementation requires shared schemas
  return { success: true, data: raw as Record<string, unknown> };
}

/**
 * Validate clue from server or WebSocket
 */
export function validateClue(raw: unknown): ValidationResult<Record<string, unknown>> {
  // Placeholder - actual implementation requires shared schemas
  return { success: true, data: raw as Record<string, unknown> };
}

/**
 * Validate role card from server or WebSocket
 */
export function validateRoleCard(raw: unknown): ValidationResult<Record<string, unknown>> {
  // Placeholder - actual implementation requires shared schemas
  return { success: true, data: raw as Record<string, unknown> };
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
