import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SaveManager from '../../components/SaveManager'

vi.mock('../../api', () => ({
  createSave: vi.fn(),
  getSave: vi.fn(),
  loadSave: vi.fn(),
  deleteSave: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
}))

import { createSave, getSave, loadSave, deleteSave } from '../../api'

const SAVE_META = { id: 7, character_id: 1, name: 'Before the vault', created_at: '2026-07-25T20:00:00Z' }

const asMock = (fn: unknown) => fn as ReturnType<typeof vi.fn>

describe('SaveManager', () => {
  const onLoad = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    asMock(getSave).mockResolvedValue(SAVE_META)
    asMock(createSave).mockResolvedValue(SAVE_META)
    asMock(loadSave).mockResolvedValue({ status: 'loaded' })
    asMock(deleteSave).mockResolvedValue({ status: 'deleted' })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches the save on mount and shows its name', async () => {
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    expect(getSave).toHaveBeenCalledWith(1)
    await waitFor(() => expect(screen.getByText(/Before the vault/)).toBeInTheDocument())
  })

  it('shows a no-save state when there is no save', async () => {
    asMock(getSave).mockRejectedValue({ response: { status: 404 } })
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    await waitFor(() => expect(screen.getByText(/no save/i)).toBeInTheDocument())
  })

  it('Save Now creates/overwrites the save and refetches metadata', async () => {
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    await waitFor(() => expect(screen.getByText(/Before the vault/)).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /save now/i }))
    await waitFor(() => expect(createSave).toHaveBeenCalledWith(1))
    // getSave: once on mount, once after saving.
    await waitFor(() => expect(getSave).toHaveBeenCalledTimes(2))
  })

  it('Load asks for confirmation, then restores and calls onLoad', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    await waitFor(() => expect(screen.getByText(/Before the vault/)).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /load/i }))
    expect(confirmSpy).toHaveBeenCalled()
    await waitFor(() => expect(loadSave).toHaveBeenCalledWith(1))
    await waitFor(() => expect(onLoad).toHaveBeenCalled())
  })

  it('Load does nothing when confirmation is declined', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    await waitFor(() => expect(screen.getByText(/Before the vault/)).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /load/i }))
    expect(loadSave).not.toHaveBeenCalled()
    expect(onLoad).not.toHaveBeenCalled()
  })

  it('Delete asks for confirmation, then deletes and returns to no-save state', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    await waitFor(() => expect(screen.getByText(/Before the vault/)).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    await waitFor(() => expect(deleteSave).toHaveBeenCalledWith(1))
    await waitFor(() => expect(screen.getByText(/no save/i)).toBeInTheDocument())
  })

  it('disables Load and Delete when there is no save', async () => {
    asMock(getSave).mockRejectedValue({ response: { status: 404 } })
    render(<SaveManager characterId={1} onLoad={onLoad} />)
    await waitFor(() => expect(screen.getByText(/no save/i)).toBeInTheDocument())

    expect(screen.getByRole('button', { name: /load/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled()
  })
})
