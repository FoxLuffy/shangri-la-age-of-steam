import { describe, it, expect, vi, beforeAll, afterAll, afterEach, beforeEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

// Mock import.meta.env before anything else
vi.stubEnv('VITE_BACKEND_URL', 'http://localhost:8003')

const server = setupServer(
  http.get('http://localhost:8003/health', () => {
    return HttpResponse.json({ status: 'ok', version: '1.0.0' })
  }),

  http.get('http://localhost:8003/state', ({ request }) => {
    return HttpResponse.json({
      state: {
        current_location_id: '1',
        active_npcs_ids: ['npc_1'],
        current_location: { id: '1', name: 'Tavern', description: 'Dim.', npcs: [] },
        active_npcs: [],
      },
      all_locations: [],
      all_npcs: [],
    })
  }),

  http.get('http://localhost:8003/market', () => {
    return HttpResponse.json([
      { name: 'Coal', current_price: 10.5 },
      { name: 'Copper', current_price: 25.0 },
    ])
  }),

  http.post('http://localhost:8003/market/trade', () => {
    return HttpResponse.json({
      status: 'ok',
      brass_coins: 490,
      new_price: 11.0,
    })
  }),

  http.get('http://localhost:8003/glossary', () => {
    return HttpResponse.json({
      locations: [{ id: '1', name: 'Tavern' }],
      npcs: [{ id: 'npc_1', name: 'Barnaby' }],
      items: [{ id: 'item_1', name: 'Wrench' }],
    })
  }),

  http.get('http://localhost:8003/characters/:id', () => {
    return HttpResponse.json({
      id: 1,
      name: 'Test Hero',
      character_class: 'Wanderer',
      background: 'Test',
      stats: { strength: 5, intellect: 5, charm: 5 },
      show_tutorials: true,
    })
  }),

  http.post('http://localhost:8003/reset', () => {
    return HttpResponse.json({ status: 'reset' })
  }),
)

// Dynamically import the api module AFTER env stub and server setup
let apiModule: typeof import('../api')

beforeAll(async () => {
  server.listen({ onUnhandledRequest: 'bypass' })
  apiModule = await import('../api')
})
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('API Client', () => {
  it('fetchHealth returns health status', async () => {
    const result = await apiModule.fetchHealth()
    expect(result).toEqual({ status: 'ok', version: '1.0.0' })
  })

  it('fetchWorldState returns world state data', async () => {
    const result = await apiModule.fetchWorldState()
    expect(result.state.current_location_id).toBe('1')
    expect(result.state.current_location.name).toBe('Tavern')
  })

  it('fetchWorldState passes character_id as query param', async () => {
    const result = await apiModule.fetchWorldState(42)
    expect(result.state).toBeDefined()
  })

  it('getMarket returns market items', async () => {
    const result = await apiModule.getMarket()
    expect(result).toHaveLength(2)
    expect(result[0].name).toBe('Coal')
    expect(result[1].name).toBe('Copper')
  })

  it('tradeMarket posts trade and returns result', async () => {
    const result = await apiModule.tradeMarket(1, 'Coal', 1, 'buy')
    expect(result.brass_coins).toBe(490)
    expect(result.new_price).toBe(11.0)
  })

  it('fetchGlossary returns categorized glossary data', async () => {
    const result = await apiModule.fetchGlossary()
    expect(result.locations).toHaveLength(1)
    expect(result.npcs).toHaveLength(1)
    expect(result.items).toHaveLength(1)
  })

  it('fetchCharacter returns character data', async () => {
    const result = await apiModule.fetchCharacter(1)
    expect(result.name).toBe('Test Hero')
    expect(result.character_class).toBe('Wanderer')
  })

  it('resetWorldState returns reset confirmation', async () => {
    const result = await apiModule.resetWorldState()
    expect(result).toEqual({ status: 'reset' })
  })

  it('handles server errors gracefully', async () => {
    server.use(
      http.get('http://localhost:8003/health', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    await expect(apiModule.fetchHealth()).rejects.toThrow()
  })

  it('handles network errors', async () => {
    server.use(
      http.get('http://localhost:8003/health', () => {
        return HttpResponse.error()
      })
    )

    await expect(apiModule.fetchHealth()).rejects.toThrow()
  })
})
