import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import MarketUI from '../../components/MarketUI'

// Mock the API module
vi.mock('../../api', () => ({
  getMarket: vi.fn(),
  tradeMarket: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
  WS_URL: 'ws://localhost:8003/ws',
}))

import { getMarket, tradeMarket } from '../../api'

const mockCharacter = {
  id: 1,
  name: 'Test Hero',
  brass_coins: 500,
}

describe('MarketUI', () => {
  const mockOnClose = vi.fn()
  const mockOnUpdateCharacter = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    ;(getMarket as ReturnType<typeof vi.fn>).mockResolvedValue([
      { name: 'Coal', current_price: 10.5 },
      { name: 'Copper', current_price: 25.0 },
    ])
  })

  it('renders without crashing', async () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    expect(screen.getByText('Global Resource Exchange')).toBeInTheDocument()
  })

  it('displays the close button', () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    const closeBtn = screen.getByText('✕')
    expect(closeBtn).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    fireEvent.click(screen.getByText('✕'))
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('displays character balance', () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    expect(screen.getByText('Account Balance')).toBeInTheDocument()
    expect(screen.getByText(/500/)).toBeInTheDocument()
  })

  it('displays 0 balance when character has no coins', () => {
    render(
      <MarketUI
        character={{ id: 1, name: 'Broke', brass_coins: 0 }}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    expect(screen.getByText(/^0/)).toBeInTheDocument()
  })

  it('shows loading message when market items are empty', () => {
    ;(getMarket as ReturnType<typeof vi.fn>).mockResolvedValue([])
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    expect(screen.getByText(/Connecting to global exchange ticker/)).toBeInTheDocument()
  })

  it('loads and displays market items', async () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    
    await waitFor(() => {
      expect(screen.getByText('Coal')).toBeInTheDocument()
      expect(screen.getByText('Copper')).toBeInTheDocument()
    })
  })

  it('displays buy and sell buttons for each item', async () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    
    await waitFor(() => {
      const buyButtons = screen.getAllByText('Buy 1')
      const sellButtons = screen.getAllByText('Sell 1')
      expect(buyButtons).toHaveLength(2)
      expect(sellButtons).toHaveLength(2)
    })
  })

  it('calls getMarket on mount', () => {
    render(
      <MarketUI
        character={mockCharacter}
        onClose={mockOnClose}
        onUpdateCharacter={mockOnUpdateCharacter}
      />
    )
    expect(getMarket).toHaveBeenCalledTimes(1)
  })
})
