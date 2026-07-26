import { describe, it, expect } from 'vitest'
import { formatEvent } from '../../utils/formatEvent'

describe('formatEvent', () => {
  it('passes through non-empty strings', () => {
    expect(formatEvent('The gaslights flicker.')).toBe('The gaslights flicker.')
    expect(formatEvent('  ')).toBeNull()
  })

  it('prefers a human-readable field on objects', () => {
    expect(formatEvent({ type: 'x', description: 'Steam floods the hall.' })).toBe('Steam floods the hall.')
    expect(formatEvent({ event_text: 'A riot erupts.' })).toBe('A riot erupts.')
  })

  it('summarizes npc_state_change in-world', () => {
    expect(formatEvent({ type: 'npc_state_change', npc: { name: 'Barnaby', hp: 100 } })).toBe('Barnaby reacts.')
    expect(formatEvent({ type: 'npc_state_change', npc: { name: 'Barnaby', hp: 0 } })).toBe('Barnaby has fallen.')
  })

  it('humanizes a bare type rather than dumping JSON', () => {
    expect(formatEvent({ type: 'market_shift' })).toBe('Market Shift')
  })

  it('returns null for un-summarizable objects (no raw JSON)', () => {
    expect(formatEvent({ foo: 1, bar: { baz: 2 } })).toBeNull()
    expect(formatEvent(null)).toBeNull()
    expect(formatEvent(42)).toBeNull()
  })
})
