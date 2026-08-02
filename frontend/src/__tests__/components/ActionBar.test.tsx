import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ActionBar from '../../components/ActionBar'

const baseProps = {
  input: 'attack the golem',
  setInput: vi.fn(),
  selectedMood: '',
  setSelectedMood: vi.fn(),
  isExploration: false,
  setIsExploration: vi.fn(),
  isLoading: false,
  isMinigameActive: false,
  isMyTurn: false, // an NPC "has initiative" — must NOT lock the player out anymore
  currentTurnActor: 'Iron Golem',
  onSubmit: vi.fn(),
}

describe('ActionBar', () => {
  it('keeps the input usable during combat (no initiative lockout — report #11)', () => {
    render(<ActionBar {...baseProps} isCombat />)
    const input = screen.getByPlaceholderText(/Your move/i) as HTMLInputElement
    expect(input).not.toBeDisabled()
    const send = screen.getByRole('button', { name: /send/i })
    expect(send).not.toBeDisabled()
  })

  it('disables the input during a minigame', () => {
    render(<ActionBar {...baseProps} isMinigameActive isCombat={false} />)
    const input = screen.getByPlaceholderText(/Focus on the minigame/i) as HTMLInputElement
    expect(input).toBeDisabled()
  })
})
