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

const BOARD = {
  available: [
    { id: 1, title: 'Rogue Automata', description: 'Track it down.', target_npc_type: 'Automata', reward_coins: 120, status: 'available' },
  ],
  active_ids: [],
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

  it('accepts a contract through the api client', async () => {
    render(<BountyBoard isOpen characterId={7} onClose={onClose} />)
    await screen.findByText('Rogue Automata')

    fireEvent.click(screen.getByRole('button', { name: /accept contract/i }))
    await waitFor(() => expect(acceptBounty).toHaveBeenCalledWith(7, 1))
    // Optimistically removed from the available list.
    await waitFor(() => expect(screen.queryByText('Rogue Automata')).not.toBeInTheDocument())
  })

  it('renders nothing when closed', () => {
    const { container } = render(<BountyBoard isOpen={false} characterId={7} onClose={onClose} />)
    expect(container).toBeEmptyDOMElement()
    expect(fetchBounties).not.toHaveBeenCalled()
  })
})
