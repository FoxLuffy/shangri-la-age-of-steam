import { describe, it, expect } from 'vitest'
import {
  factionColor,
  easeInOutQuad,
  travelPoint,
  altitudeForProgress,
  humanizeFactionId,
  NEUTRAL_COLOR,
} from '../../utils/worldMapUtils'

describe('worldMapUtils', () => {
  describe('factionColor', () => {
    it('is deterministic for the same id', () => {
      expect(factionColor('iron_syndicate')).toBe(factionColor('iron_syndicate'))
    })

    it('returns the neutral color for empty ids', () => {
      expect(factionColor(undefined)).toBe(NEUTRAL_COLOR)
      expect(factionColor(null)).toBe(NEUTRAL_COLOR)
      expect(factionColor('')).toBe(NEUTRAL_COLOR)
    })

    it('distinguishes at least some different factions', () => {
      const colors = new Set(['a', 'b', 'c', 'd'].map(factionColor))
      expect(colors.size).toBeGreaterThan(1)
    })
  })

  describe('easeInOutQuad', () => {
    it('maps endpoints and midpoint', () => {
      expect(easeInOutQuad(0)).toBe(0)
      expect(easeInOutQuad(1)).toBe(1)
      expect(easeInOutQuad(0.5)).toBeCloseTo(0.5, 5)
    })
  })

  describe('travelPoint', () => {
    const from = { x: 0, y: 0 }
    const to = { x: 10, y: 20 }
    it('returns endpoints at 0 and 1', () => {
      expect(travelPoint(from, to, 0)).toEqual({ x: 0, y: 0 })
      expect(travelPoint(from, to, 1)).toEqual({ x: 10, y: 20 })
    })
    it('returns the midpoint at 0.5', () => {
      expect(travelPoint(from, to, 0.5)).toEqual({ x: 5, y: 10 })
    })
  })

  describe('altitudeForProgress', () => {
    it('is 0 at the ends and peaks at the middle', () => {
      expect(altitudeForProgress(0, 100)).toBeCloseTo(0, 5)
      expect(altitudeForProgress(1, 100)).toBeCloseTo(0, 5)
      expect(altitudeForProgress(0.5, 100)).toBeCloseTo(100, 5)
    })
    it('stays within [0, max]', () => {
      for (let p = 0; p <= 1.0001; p += 0.1) {
        const alt = altitudeForProgress(p, 100)
        expect(alt).toBeGreaterThanOrEqual(0)
        expect(alt).toBeLessThanOrEqual(100)
      }
    })
  })

  describe('humanizeFactionId', () => {
    it('title-cases and de-underscores', () => {
      expect(humanizeFactionId('iron_syndicate')).toBe('Iron Syndicate')
      expect(humanizeFactionId('alchemists')).toBe('Alchemists')
    })
  })
})
