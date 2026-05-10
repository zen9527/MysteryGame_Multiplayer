import { describe, it, expect } from 'vitest';
import { parseSSELine } from '../../src/utils/sse';

describe('SSE Parser', () => {
  it('parses valid SSE data line with JSON', () => {
    const result = parseSSELine('data: {"type":"chunk","content":"hello"}');
    expect(result).toEqual({ type: 'chunk', data: { type: 'chunk', content: 'hello' } });
  });

  it('parses SSE start event', () => {
    const result = parseSSELine('data: {"type":"start"}');
    expect(result).toEqual({ type: 'start', data: { type: 'start' } });
  });

  it('parses SSE done event', () => {
    const result = parseSSELine('data: {"type":"done","content":"full text"}');
    expect(result).toEqual({ type: 'done', data: { type: 'done', content: 'full text' } });
  });

  it('parses SSE error event', () => {
    const result = parseSSELine('data: {"type":"error","message":"something failed"}');
    expect(result).toEqual({ type: 'error', data: { type: 'error', message: 'something failed' } });
  });

  it('returns null for empty line', () => {
    expect(parseSSELine('')).toBeNull();
  });

  it('returns null for comment line', () => {
    expect(parseSSELine(': comment')).toBeNull();
  });

  it('returns null for non-data line', () => {
    expect(parseSSELine('id: 123')).toBeNull();
    expect(parseSSELine('event: message')).toBeNull();
  });

  it('returns null for invalid JSON in data', () => {
    expect(parseSSELine('data: not-json')).toBeNull();
  });

  it('handles whitespace-only line', () => {
    expect(parseSSELine('   ')).toBeNull();
  });

  it('defaults type to chunk if missing', () => {
    const result = parseSSELine('data: {"content":"test"}');
    expect(result).toEqual({ type: 'chunk', data: { content: 'test' } });
  });

  it('handles Chinese content in SSE data', () => {
    const result = parseSSELine('data: {"type":"chunk","content":"你好世界"}');
    expect(result).toEqual({ type: 'chunk', data: { type: 'chunk', content: '你好世界' } });
  });
});
