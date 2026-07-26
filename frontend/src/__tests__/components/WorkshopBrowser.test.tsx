import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { WorkshopBrowser } from '../../components/WorkshopBrowser'

vi.mock('../../api', () => ({
  fetchWorkshopMods: vi.fn(),
  installWorkshopMod: vi.fn(),
  rateMod: vi.fn(),
  fetchModRatings: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
}))

import { fetchWorkshopMods, installWorkshopMod, rateMod } from '../../api'

const asMock = (fn: unknown) => fn as ReturnType<typeof vi.fn>

const MODS = [
  { id: 'mod_1', name: 'Expanded Locations', description: 'More places.', author: 'A', downloads: 1205, avg_rating: 4.8, rating_count: 3, featured: true },
  { id: 'mod_2', name: 'New Factions', description: 'Sky pirates.', author: 'B', downloads: 842, avg_rating: 3.0, rating_count: 1, featured: false },
]

describe('WorkshopBrowser', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    asMock(fetchWorkshopMods).mockResolvedValue(MODS)
    asMock(installWorkshopMod).mockResolvedValue({ message: 'ok' })
    asMock(rateMod).mockResolvedValue({ avg_rating: 5, rating_count: 4 })
  })

  it('renders mods with rating average and downloads', async () => {
    render(<WorkshopBrowser userId={1} />)
    await waitFor(() => {
      expect(screen.getByText('New Factions')).toBeInTheDocument()
      expect(screen.getAllByText(/4\.8/).length).toBeGreaterThan(0)
      expect(screen.getByText(/1205/)).toBeInTheDocument()
    })
  })

  it('shows a featured section containing the featured mod', async () => {
    render(<WorkshopBrowser userId={1} />)
    const featured = await screen.findByTestId('featured-carousel')
    expect(within(featured).getByText('Expanded Locations')).toBeInTheDocument()
  })

  it('submits a star rating', async () => {
    render(<WorkshopBrowser userId={9} />)
    await waitFor(() => expect(screen.getByText('New Factions')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /rate mod_2 5 stars/i }))
    await waitFor(() => expect(rateMod).toHaveBeenCalledWith('mod_2', 9, 5))
  })

  it('installs a mod', async () => {
    render(<WorkshopBrowser userId={1} />)
    await waitFor(() => expect(screen.getByText('New Factions')).toBeInTheDocument())
    const installButtons = screen.getAllByRole('button', { name: /^install$/i })
    fireEvent.click(installButtons[0])
    await waitFor(() => expect(installWorkshopMod).toHaveBeenCalled())
  })
})
