import { describe, it, expect } from 'vitest';
import { validateChatMessage, validateClue, validateRoleCard, validateBatch, logValidationError } from '@/utils/schema-validation';

describe('schema-validation', () => {
  describe('validateChatMessage', () => {
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
    
    it('rejects invalid chat message with empty content', () => {
      const result = validateChatMessage({
        message_id: '1',
        content: '', // Empty content should fail min_length
        player_id: 'p1',
        role_name: 'Detective',
        timestamp: '2026-05-11T12:00:00Z',
        from_player_name: 'Alice'
      });
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('too_small');
    });
    
    it('rejects chat message with missing required fields', () => {
      const result = validateChatMessage({
        message_id: '1',
        content: 'Hello'
        // Missing player_id, role_name, timestamp, from_player_name
      });
      
      expect(result.success).toBe(false);
    });
  });

  describe('validateClue', () => {
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
    
    it('rejects clue with invalid unlock_phase', () => {
      const result = validateClue({
        id: 'clue1',
        title: 'Secret Letter',
        content: 'The will was forged',
        unlock_phase: 'act3' as any, // Invalid phase
        clue_type: 'public'
      });
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('invalid_value');
    });
    
    it('validates clue with optional related_role_id', () => {
      const result = validateClue({
        id: 'clue1',
        title: 'Secret Letter',
        content: 'The will was forged',
        unlock_phase: 'act1',
        clue_type: 'private',
        related_role_id: 'role1'
      });
      
      expect(result.success).toBe(true);
      expect(result.data?.related_role_id).toBe('role1');
    });
  });

  describe('validateRoleCard', () => {
    it('validates correct role card', () => {
      const result = validateRoleCard({
        role_id: 'role1',
        role_name: 'Detective',
        player_id: 'p1',
        layer: 1,
        content: 'You are the detective.'
      });
      
      expect(result.success).toBe(true);
      expect(result.data?.role_name).toBe('Detective');
    });
    
    it('rejects role card with invalid layer', () => {
      const result = validateRoleCard({
        role_id: 'role1',
        role_name: 'Detective',
        player_id: 'p1',
        layer: 5 as any, // Invalid layer (must be 1-3)
        content: 'You are the detective.'
      });
      
      expect(result.success).toBe(false);
    });
    
    it('validates role card with optional secrets', () => {
      const result = validateRoleCard({
        role_id: 'role1',
        role_name: 'Detective',
        player_id: 'p1',
        layer: 2,
        content: 'You are the detective.',
        secrets: ['I saw something suspicious']
      });
      
      expect(result.success).toBe(true);
      expect(result.data?.secrets).toEqual(['I saw something suspicious']);
    });
  });

  describe('validateBatch', () => {
    it('validates batch of chat messages', () => {
      const messages = [
        {
          message_id: '1',
          content: 'Hello',
          player_id: 'p1',
          role_name: 'Detective',
          timestamp: '2026-05-11T12:00:00Z',
          from_player_name: 'Alice'
        },
        {
          message_id: '2',
          content: '', // Invalid
          player_id: 'p2',
          role_name: 'Suspect',
          timestamp: '2026-05-11T12:01:00Z',
          from_player_name: 'Bob'
        }
      ];
      
      const result = validateBatch(messages, validateChatMessage);
      
      expect(result.valid.length).toBe(1);
      expect(result.invalid.length).toBe(1);
      expect(result.invalid[0].error).toContain('too_small');
    });
  });

  describe('logValidationError', () => {
    it('logs error in development mode', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      logValidationError('TestContext', 'Test error message');
      
      // In dev mode, should log
      if (import.meta.env.DEV) {
        expect(consoleSpy).toHaveBeenCalledWith('[TestContext] Validation error:', 'Test error message');
      }
      
      consoleSpy.mockRestore();
    });
  });
});
