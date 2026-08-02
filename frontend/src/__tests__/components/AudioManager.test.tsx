import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import AudioManager from '../../components/AudioManager'

// Minimal Web Audio stub — jsdom has no AudioContext.
function makeParam() {
  return {
    value: 0,
    setValueAtTime: vi.fn(),
    setTargetAtTime: vi.fn(),
    linearRampToValueAtTime: vi.fn(),
    exponentialRampToValueAtTime: vi.fn(),
    cancelScheduledValues: vi.fn(),
  }
}

let createBufferSourceCalls = 0
let closeSpy: ReturnType<typeof vi.fn>

class MockAudioContext {
  currentTime = 0
  sampleRate = 44100
  destination = {}
  close = (closeSpy = vi.fn())
  createOscillator() {
    return { type: '', frequency: makeParam(), connect: vi.fn(), start: vi.fn() }
  }
  createGain() {
    return { gain: makeParam(), connect: vi.fn() }
  }
  createBuffer() {
    return { getChannelData: () => new Float32Array(10) }
  }
  createBufferSource() {
    createBufferSourceCalls++
    return { buffer: null, connect: vi.fn(), start: vi.fn() }
  }
}

describe('AudioManager', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    createBufferSourceCalls = 0
    ;(window as any).AudioContext = MockAudioContext as any
    localStorage.setItem('saos_audio_enabled', 'true')
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('clears ambient/music intervals on unmount so bursts do not stack (report #2)', () => {
    const { unmount } = render(<AudioManager locationId="1" mood="" />)
    // User gesture starts the audio context + ambient hiss interval.
    fireEvent.click(window)

    // Ambient hiss fires on its 5s interval while mounted.
    vi.advanceTimersByTime(5000)
    const whileMounted = createBufferSourceCalls
    expect(whileMounted).toBeGreaterThan(0)
    expect(closeSpy).not.toHaveBeenCalled()

    unmount()
    expect(closeSpy).toHaveBeenCalled() // context torn down

    // After unmount the hiss interval is cleared — no further bursts (no leak/stacking).
    vi.advanceTimersByTime(20000)
    expect(createBufferSourceCalls).toBe(whileMounted)
  })
})
