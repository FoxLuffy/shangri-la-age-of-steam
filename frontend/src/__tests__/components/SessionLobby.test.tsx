import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SessionLobby from '../../components/SessionLobby'

describe('SessionLobby', () => {
  const mockOnSessionSelect = vi.fn()

  beforeEach(() => {
    mockOnSessionSelect.mockClear()
  })

  it('renders without crashing', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    expect(screen.getByText('UPLINK ESTABLISHED: SELECT PROTOCOL')).toBeInTheDocument()
  })

  it('displays all four tab buttons', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    expect(screen.getByText('Solo Protocol')).toBeInTheDocument()
    expect(screen.getByText('Host Co-Op')).toBeInTheDocument()
    expect(screen.getByText('Public Lobbies')).toBeInTheDocument()
    expect(screen.getByText('Join Private')).toBeInTheDocument()
  })

  it('shows solo tab content by default with commence button', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    expect(screen.getByText('Commence Solo Journey')).toBeInTheDocument()
  })

  it('calls onSessionSelect with "solo" when solo button clicked', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Commence Solo Journey'))
    expect(mockOnSessionSelect).toHaveBeenCalledWith('solo')
  })

  it('switches to host tab and shows host content', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Host Co-Op'))
    expect(screen.getByText('Initialize Host Node')).toBeInTheDocument()
  })

  it('calls onSessionSelect with "host" and password when host button clicked', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Host Co-Op'))
    fireEvent.click(screen.getByText('Initialize Host Node'))
    expect(mockOnSessionSelect).toHaveBeenCalledWith('host', undefined, '')
  })

  it('switches to join private tab and shows session ID input', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Join Private'))
    expect(screen.getByText('Authenticate & Join')).toBeInTheDocument()
    expect(screen.getByText('Session ID')).toBeInTheDocument()
    // Session ID text input is present
    const textInputs = screen.getAllByRole('textbox')
    expect(textInputs.length).toBeGreaterThanOrEqual(1)
  })

  it('disables join private button when session ID is empty', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Join Private'))
    const joinBtn = screen.getByText('Authenticate & Join')
    expect(joinBtn).toBeDisabled()
  })

  it('enables join private button when session ID is entered', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Join Private'))
    // The session ID input is the text input (not the password input)
    const textInput = screen.getByRole('textbox')
    fireEvent.change(textInput, { target: { value: 'test-session-123' } })
    const joinBtn = screen.getByText('Authenticate & Join')
    expect(joinBtn).not.toBeDisabled()
  })

  it('switches to public lobbies tab and shows no sessions message', () => {
    render(<SessionLobby onSessionSelect={mockOnSessionSelect} />)
    fireEvent.click(screen.getByText('Public Lobbies'))
    expect(screen.getByText('Refresh Scan')).toBeInTheDocument()
    expect(screen.getByText(/No public sessions detected/)).toBeInTheDocument()
  })
})
