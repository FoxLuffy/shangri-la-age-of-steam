import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import GuildPanel from '../../components/GuildPanel'

vi.mock('../../api', () => ({
  fetchMyGuild: vi.fn(),
  createGuild: vi.fn(),
  inviteGuild: vi.fn(),
}))

import { fetchMyGuild, createGuild } from '../../api'
const asMock = (fn: unknown) => fn as ReturnType<typeof vi.fn>

const NO_GUILD = { guild: null, members: [], is_leader: false }
const WITH_GUILD = {
  guild: { id: 1, name: 'Iron Circle', description: 'A steely brotherhood', treasury: 0, leader_id: 7 },
  members: [{ id: 7, name: 'Founder', is_leader: true }],
  is_leader: true,
}

describe('GuildPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    asMock(createGuild).mockResolvedValue({ id: 1 })
  })

  it('shows the create form when the character has no guild', async () => {
    asMock(fetchMyGuild).mockResolvedValue(NO_GUILD)
    render(<GuildPanel characterId={7} onClose={() => {}} />)
    expect(await screen.findByPlaceholderText('Guild Name')).toBeInTheDocument()
  })

  it('shows the created guild immediately after creation (no reopen)', async () => {
    // First load: no guild. After create: refetch returns the new guild.
    asMock(fetchMyGuild).mockResolvedValueOnce(NO_GUILD).mockResolvedValueOnce(WITH_GUILD)
    render(<GuildPanel characterId={7} onClose={() => {}} />)

    const nameInput = await screen.findByPlaceholderText('Guild Name')
    fireEvent.change(nameInput, { target: { value: 'Iron Circle' } })
    fireEvent.click(screen.getByRole('button', { name: /create guild/i }))

    await waitFor(() => expect(createGuild).toHaveBeenCalledWith(7, 'Iron Circle', ''))
    // Guild view is shown without any manual reopen.
    expect(await screen.findByText('Iron Circle')).toBeInTheDocument()
    expect(screen.getByText('Founder')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Guild Name')).not.toBeInTheDocument()
  })
})
