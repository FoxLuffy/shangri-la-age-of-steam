import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ArtifactJournal } from '../../components/ArtifactJournal'

vi.mock('../../api', () => ({
  fetchJournal: vi.fn(),
}))

import { fetchJournal } from '../../api'
const asMock = (fn: unknown) => fn as ReturnType<typeof vi.fn>

const JOURNAL = {
  places: [{ id: '1', name: 'The Rusty Anchor Tavern', description: 'A dim tavern.' }],
  people: [{ id: 'silas', name: 'Silas', traits: ['cynical'] }],
  artifacts: [
    { id: 1, name: 'Aether Compass', description: 'Points to aether.', rarity: 'Rare', stat_bonus: { intellect: 2 }, discovered: true },
    { id: 2, name: 'Ironheart Locket', description: 'Stills fear.', rarity: 'Uncommon', stat_bonus: {}, discovered: false },
  ],
}

describe('ArtifactJournal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    asMock(fetchJournal).mockResolvedValue(JOURNAL)
  })

  it('fetches via the api client (not a raw localhost URL) and renders discovery sections', async () => {
    render(<ArtifactJournal characterId={7} onClose={() => {}} />)
    await waitFor(() => expect(fetchJournal).toHaveBeenCalledWith(7))

    expect(await screen.findByText('The Rusty Anchor Tavern')).toBeInTheDocument()
    expect(screen.getByText('Silas')).toBeInTheDocument()
    // Discovered artifact shows its name; undiscovered stays hidden.
    expect(screen.getByText('Aether Compass')).toBeInTheDocument()
    expect(screen.getByText('Unknown Artifact')).toBeInTheDocument()
    expect(screen.queryByText('Ironheart Locket')).not.toBeInTheDocument()
  })

  it('shows empty-state copy when nothing is discovered yet', async () => {
    asMock(fetchJournal).mockResolvedValue({ places: [], people: [], artifacts: [] })
    render(<ArtifactJournal characterId={7} onClose={() => {}} />)
    expect(await screen.findByText(/have not yet ventured/i)).toBeInTheDocument()
    expect(screen.getByText(/have not yet met anyone/i)).toBeInTheDocument()
  })
})
