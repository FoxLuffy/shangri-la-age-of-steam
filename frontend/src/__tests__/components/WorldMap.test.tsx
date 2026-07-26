import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import WorldMap from '../../components/WorldMap'

vi.mock('../../api', () => ({
  fetchAirship: vi.fn(() => Promise.resolve(null)),
  navigateAirship: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
}))

const LOCATIONS = [
  { id: '1', name: 'Grand Foundry', description: '', npcs: [], faction_id: 'iron_syndicate' },
  { id: '2', name: 'Observatory', description: '', npcs: [], faction_id: 'alchemists' },
  { id: '3', name: 'Undercity', description: '', npcs: [], faction_id: null },
]

describe('WorldMap', () => {
  beforeEach(() => vi.clearAllMocks())

  const props = {
    currentLocationId: '1',
    characterId: 1,
    onLocationSelect: vi.fn(),
    onClose: vi.fn(),
  }

  it('renders without crashing', () => {
    render(<WorldMap locations={LOCATIONS} {...props} />)
    expect(screen.getByText(/World Map/i)).toBeInTheDocument()
  })

  it('shows a faction legend with humanized names', () => {
    render(<WorldMap locations={LOCATIONS} {...props} />)
    expect(screen.getByText('Territories')).toBeInTheDocument()
    expect(screen.getByText('Iron Syndicate')).toBeInTheDocument()
    expect(screen.getByText('Alchemists')).toBeInTheDocument()
  })

  it('omits the legend when no locations have a faction', () => {
    const plain = LOCATIONS.map((l) => ({ ...l, faction_id: null }))
    render(<WorldMap locations={plain} {...props} />)
    expect(screen.queryByText('Territories')).not.toBeInTheDocument()
  })
})
