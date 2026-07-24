import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatInterface from '../../components/ChatInterface'

// Mock the API module
vi.mock('../../api', () => ({
  fetchWorldState: vi.fn(),
  sendAction: vi.fn(),
  resetWorldState: vi.fn(),
  importWorldState: vi.fn(),
  fetchGlossary: vi.fn(),
  fetchHistory: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
  WS_URL: 'ws://localhost:8003/ws',
}))

// Mock WebSocket as a class
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  
  readyState = MockWebSocket.OPEN
  onopen: ((ev: Event) => void) | null = null
  onclose: ((ev: CloseEvent) => void) | null = null
  onmessage: ((ev: MessageEvent) => void) | null = null
  onerror: ((ev: Event) => void) | null = null
  
  constructor(_url: string) {}
  addEventListener() {}
  removeEventListener() {}
  close() { this.readyState = MockWebSocket.CLOSED }
  send() {}
}

vi.stubGlobal('WebSocket', MockWebSocket)

import { fetchWorldState, sendAction, fetchGlossary } from '../../api'

const mockWorldState = {
  state: {
    current_location_id: '1',
    active_npcs_ids: ['npc_1'],
    global_event: null,
    current_location: { id: '1', name: 'The Rusty Anchor Tavern', description: 'A dim tavern.', npcs: ['npc_1'] },
    active_npcs: [
      { id: 'npc_1', name: 'Barnaby', traits: ['cautious'], disposition: 0.3, memories: [] },
    ],
    inventory: [],
    quests: [],
  },
  all_locations: [
    { id: '1', name: 'The Rusty Anchor Tavern', description: 'A dim tavern.', npcs: ['npc_1'] },
    { id: '2', name: 'Clockwork Plaza', description: 'A bustling plaza.', npcs: [] },
  ],
  all_npcs: [
    { id: 'npc_1', name: 'Barnaby', traits: ['cautious'], disposition: 0.3, memories: [] },
  ],
  active_players: [],
}

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(fetchWorldState as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorldState)
    ;(fetchGlossary as ReturnType<typeof vi.fn>).mockResolvedValue({
      locations: [], npcs: [], items: [],
    })
    ;(sendAction as ReturnType<typeof vi.fn>).mockResolvedValue({
      narration: 'The tavern is quiet.',
    })
    localStorage.clear()
  })

  it('renders without crashing', async () => {
    render(<ChatInterface characterId={1} />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Type your action/i)).toBeInTheDocument()
    })
  })

  it('displays the action input field', async () => {
    render(<ChatInterface characterId={1} />)
    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your action/i)
      expect(input).toBeInTheDocument()
    })
  })

  it('loads world state on mount', async () => {
    render(<ChatInterface characterId={1} />)
    await waitFor(() => {
      expect(fetchWorldState).toHaveBeenCalledWith(1)
    })
  })

  it('shows location name after state loads', async () => {
    render(<ChatInterface characterId={1} />)
    await waitFor(() => {
      const matches = screen.getAllByText(/Rusty Anchor Tavern/)
      expect(matches.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('allows typing in the action input', async () => {
    render(<ChatInterface characterId={1} />)
    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your action/i) as HTMLInputElement
      fireEvent.change(input, { target: { value: 'Look around the tavern' } })
      expect(input.value).toBe('Look around the tavern')
    })
  })

  it('calls onStateUpdate callback when provided', async () => {
    const mockOnStateUpdate = vi.fn()
    render(<ChatInterface characterId={1} onStateUpdate={mockOnStateUpdate} />)
    await waitFor(() => {
      expect(mockOnStateUpdate).toHaveBeenCalled()
    })
  })

  it('renders with no characterId gracefully', () => {
    render(<ChatInterface />)
    expect(screen.getByPlaceholderText(/Type your action/i)).toBeInTheDocument()
  })
})
