import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  AUTOSAVE_EVERY,
  resetAutosaveCounter,
  recordActionAndMaybeAutosave,
  autosaveBeforeTravel,
} from '../../utils/autosave'

describe('autosave', () => {
  beforeEach(() => {
    resetAutosaveCounter()
  })

  it('saves only on every Nth action', async () => {
    const save = vi.fn().mockResolvedValue({})
    for (let i = 1; i < AUTOSAVE_EVERY; i++) {
      const fired = await recordActionAndMaybeAutosave(1, save)
      expect(fired).toBe(false)
    }
    expect(save).not.toHaveBeenCalled()

    const fired = await recordActionAndMaybeAutosave(1, save)
    expect(fired).toBe(true)
    expect(save).toHaveBeenCalledTimes(1)
    expect(save).toHaveBeenCalledWith(1)
  })

  it('saves again after another N actions', async () => {
    const save = vi.fn().mockResolvedValue({})
    for (let i = 0; i < AUTOSAVE_EVERY * 2; i++) {
      await recordActionAndMaybeAutosave(1, save)
    }
    expect(save).toHaveBeenCalledTimes(2)
  })

  it('resetAutosaveCounter restarts the cadence', async () => {
    const save = vi.fn().mockResolvedValue({})
    await recordActionAndMaybeAutosave(1, save)
    await recordActionAndMaybeAutosave(1, save)
    resetAutosaveCounter()
    for (let i = 1; i < AUTOSAVE_EVERY; i++) {
      await recordActionAndMaybeAutosave(1, save)
    }
    expect(save).not.toHaveBeenCalled()
    await recordActionAndMaybeAutosave(1, save)
    expect(save).toHaveBeenCalledTimes(1)
  })

  it('autosaveBeforeTravel saves once with the character id', async () => {
    const save = vi.fn().mockResolvedValue({})
    const ok = await autosaveBeforeTravel(42, save)
    expect(ok).toBe(true)
    expect(save).toHaveBeenCalledTimes(1)
    expect(save).toHaveBeenCalledWith(42)
  })

  it('swallows save errors and does not throw', async () => {
    const save = vi.fn().mockRejectedValue(new Error('network down'))
    await expect(autosaveBeforeTravel(1, save)).resolves.toBe(false)

    for (let i = 1; i < AUTOSAVE_EVERY; i++) {
      await recordActionAndMaybeAutosave(1, save)
    }
    await expect(recordActionAndMaybeAutosave(1, save)).resolves.toBe(false)
  })
})
