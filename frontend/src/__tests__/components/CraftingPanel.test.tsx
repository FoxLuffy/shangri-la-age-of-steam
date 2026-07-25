import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CraftingPanel from '../../components/CraftingPanel'

vi.mock('../../api', () => ({
  getKnownRecipes: vi.fn(),
  getCraftingMaterials: vi.fn(),
  getProficiency: vi.fn(),
  craftItem: vi.fn(),
  experimentCraft: vi.fn(),
  craftSuccessPct: (level: number, tier: number, branch: string | null) =>
    branch ? Math.round(Math.max(5, Math.min(98, 50 + 10 * (level - tier)))) : 100,
  BACKEND_URL: 'http://localhost:8003',
}))

import { getKnownRecipes, getCraftingMaterials, getProficiency, craftItem, experimentCraft } from '../../api'

const asMock = (fn: unknown) => fn as ReturnType<typeof vi.fn>

const RECIPE = {
  recipe_id: 1,
  name: 'Forge Blade',
  method: 'dialogue',
  branch: 'metallurgy',
  tier: 1,
  result_item_id: 9,
  result_name: 'Blade',
  requirements: [{ item_id: 5, name: 'Ore', quantity: 2 }],
}

const MATERIALS = [{ item_id: 5, name: 'Ore', quantity: 4 }]
const PROFICIENCY = [
  { branch: 'metallurgy', level: 2, xp: 6 },
  { branch: 'alchemy', level: 0, xp: 0 },
  { branch: 'clockwork', level: 0, xp: 0 },
]

describe('CraftingPanel', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    asMock(getKnownRecipes).mockResolvedValue([RECIPE])
    asMock(getCraftingMaterials).mockResolvedValue(MATERIALS)
    asMock(getProficiency).mockResolvedValue(PROFICIENCY)
    asMock(craftItem).mockResolvedValue({ crafted: true })
    asMock(experimentCraft).mockResolvedValue({ discovered: null })
  })

  it('renders proficiency branch bars', async () => {
    render(<CraftingPanel characterId={1} onClose={onClose} />)
    await waitFor(() => {
      expect(screen.getAllByText(/metallurgy/i).length).toBeGreaterThan(0)
      expect(screen.getByText(/alchemy/i)).toBeInTheDocument()
      expect(screen.getByText(/clockwork/i)).toBeInTheDocument()
    })
  })

  it('renders a known recipe with its name and success percentage', async () => {
    render(<CraftingPanel characterId={1} onClose={onClose} />)
    await waitFor(() => {
      expect(screen.getByText('Forge Blade')).toBeInTheDocument()
      // level 2, tier 1 -> 50 + 10*(1) = 60%
      expect(screen.getByText(/60%/)).toBeInTheDocument()
    })
  })

  it('crafts a recipe and refetches', async () => {
    render(<CraftingPanel characterId={1} onClose={onClose} />)
    await waitFor(() => expect(screen.getByText('Forge Blade')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /^craft$/i }))
    await waitFor(() => expect(craftItem).toHaveBeenCalledWith(1, 1))
    // getKnownRecipes: once on mount, once after crafting.
    await waitFor(() => expect(getKnownRecipes).toHaveBeenCalledTimes(2))
  })

  it('experiments with a selected material', async () => {
    render(<CraftingPanel characterId={1} onClose={onClose} />)
    await waitFor(() => expect(screen.getByText('Forge Blade')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /select material Ore/i }))
    fireEvent.click(screen.getByRole('button', { name: /attempt/i }))
    await waitFor(() => expect(experimentCraft).toHaveBeenCalledWith(1, [5]))
  })

  it('calls onClose when the close button is clicked', async () => {
    render(<CraftingPanel characterId={1} onClose={onClose} />)
    await waitFor(() => expect(screen.getByText('Forge Blade')).toBeInTheDocument())
    fireEvent.click(screen.getByText('✕'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
