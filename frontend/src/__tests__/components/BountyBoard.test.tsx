import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import BountyBoard from '../../components/BountyBoard'

vi.mock('../../api', () => ({
  fetchBounties: vi.fn(),
  acceptBounty: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
}))

import { fetchBounties, acceptBounty } from '../../api'

const asMock = (fn: unknown) => fn as ReturnType<typeof vi.fn>

const BOUNTY = { id: 1, title: 'Rogue Automata', description: 'Track it down.', target_npc_type: 'Automata', reward_coins: 120, status: 'available' }

const BOARD = {
  available: [BOUNTY],
  active: [],
  active_ids: [],
  completed_ids: [],
}

// After accepting, the reload returns the bounty as the single active contract.
const BOARD_AFTER_ACCEPT = {
  available: [],
  active: [{ ...BOUNTY, status: 'active' }],
  active_ids: [1],
  completed_ids: [],
}

describe('BountyBoard', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    asMock(fetchBounties).mockResolvedValue(BOARD)
    asMock(acceptBounty).mockResolvedValue({ status: 'success' })
  })

  it('loads bounties via the api client (not a raw /api fetch)', async () => {
    render(<BountyBoard isOpen characterId={7} onClose={onClose} />)
    await waitFor(() => expect(fetchBounties).toHaveBeenCalledWith(7))
    expect(await screen.findByText('Rogue Automata')).toBeInTheDocument()
  })

  it('accepts a contract and shows it as the active contract', async () => {
    asMock(fetchBounties).mockResolvedValueOnce(BOARD).mockResolvedValueOnce(BOARD_AFTER_ACCEPT)
    render(<BountyBoard isOpen characterId={7} onClose={onClose} />)
    await screen.findByText('Rogue Automata')

    fireEvent.click(screen.getByRole('button', { name: /accept contract/i }))
    await waitFor(() => expect(acceptBounty).toHaveBeenCalledWith(7, 1))
    // Reloads and surfaces the accepted bounty as the active contract.
    await waitFor(() => expect(screen.getByText(/Your Active Contract/i)).toBeInTheDocument())
    // No longer offered as an available contract to accept.
    await waitFor(() => expect(screen.queryByRole('button', { name: /accept contract/i })).not.toBeInTheDocument())
  })

  it('renders nothing when closed', () => {
    const { container } = render(<BountyBoard isOpen={false} characterId={7} onClose={onClose} />)
    expect(container).toBeEmptyDOMElement()
    expect(fetchBounties).not.toHaveBeenCalled()
  })
})
