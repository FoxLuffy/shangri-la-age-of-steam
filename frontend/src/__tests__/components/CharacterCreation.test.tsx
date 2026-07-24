import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import CharacterCreation from '../../components/CharacterCreation'

// Mock the API module
vi.mock('../../api', () => ({
  createCharacter: vi.fn(),
  generateGear: vi.fn(),
  fetchSessions: vi.fn(),
  BACKEND_URL: 'http://localhost:8003',
  WS_URL: 'ws://localhost:8003/ws',
}))

import { createCharacter, generateGear, fetchSessions } from '../../api'

describe('CharacterCreation', () => {
  const mockOnComplete = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    ;(fetchSessions as ReturnType<typeof vi.fn>).mockResolvedValue([])
    ;(createCharacter as ReturnType<typeof vi.fn>).mockResolvedValue({ id: 42 })
    ;(generateGear as ReturnType<typeof vi.fn>).mockResolvedValue([])
  })

  it('renders without crashing', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    // Without userId, it goes straight to creation form
    expect(screen.getByText('Manifest')).toBeInTheDocument()
  })

  it('shows the name input field', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    expect(screen.getByPlaceholderText('Enter your name...')).toBeInTheDocument()
  })

  it('shows all four class presets', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    expect(screen.getByText('Wanderer')).toBeInTheDocument()
    expect(screen.getByText('Aristocrat')).toBeInTheDocument()
    expect(screen.getByText('Scrapper')).toBeInTheDocument()
    expect(screen.getByText('Alchemist')).toBeInTheDocument()
  })

  it('shows preset descriptions', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    expect(screen.getByText(/Balanced stats/)).toBeInTheDocument()
    expect(screen.getByText(/High charm/)).toBeInTheDocument()
    expect(screen.getByText(/High strength/)).toBeInTheDocument()
    expect(screen.getByText(/High intellect/)).toBeInTheDocument()
  })

  it('disables submit button when name is empty', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    const submitBtn = screen.getByText('Begin Journey')
    expect(submitBtn).toBeDisabled()
  })

  it('enables submit button when name is entered', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    const nameInput = screen.getByPlaceholderText('Enter your name...')
    fireEvent.change(nameInput, { target: { value: 'Gearsworth' } })
    const submitBtn = screen.getByText('Begin Journey')
    expect(submitBtn).not.toBeDisabled()
  })

  it('calls createCharacter and onComplete on submit', async () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    
    const nameInput = screen.getByPlaceholderText('Enter your name...')
    fireEvent.change(nameInput, { target: { value: 'Gearsworth' } })
    fireEvent.click(screen.getByText('Begin Journey'))
    
    await waitFor(() => {
      expect(createCharacter).toHaveBeenCalledWith(
        'Gearsworth', 'Wanderer', '', '', true, [], undefined
      )
      expect(mockOnComplete).toHaveBeenCalledWith(42)
    })
  })

  it('shows tutorials checkbox that is checked by default', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    const checkbox = screen.getByLabelText(/Enable Interactive Tutorials/)
    expect(checkbox).toBeChecked()
  })

  it('shows backstory textarea', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    expect(screen.getByPlaceholderText(/Leave blank to use the class preset/)).toBeInTheDocument()
  })

  it('shows gear prompt textarea and generate button', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    expect(screen.getByPlaceholderText(/Describe what gear/)).toBeInTheDocument()
    expect(screen.getByText('Generate Gear')).toBeInTheDocument()
  })

  it('disables generate gear button when gear prompt is empty', () => {
    render(<CharacterCreation onComplete={mockOnComplete} />)
    const genBtn = screen.getByText('Generate Gear')
    expect(genBtn).toBeDisabled()
  })

  it('shows session selector when userId is provided and sessions exist', async () => {
    ;(fetchSessions as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: 1, name: 'Old Character', character_class: 'Scrapper' },
    ])
    
    render(<CharacterCreation onComplete={mockOnComplete} userId={5} />)
    
    await waitFor(() => {
      expect(screen.getByText('Select Session')).toBeInTheDocument()
      expect(screen.getByText('Old Character')).toBeInTheDocument()
    })
  })

  it('shows create new character button in session selector', async () => {
    ;(fetchSessions as ReturnType<typeof vi.fn>).mockResolvedValue([
      { id: 1, name: 'Old Character', character_class: 'Scrapper' },
    ])
    
    render(<CharacterCreation onComplete={mockOnComplete} userId={5} />)
    
    await waitFor(() => {
      expect(screen.getByText('Create New Character')).toBeInTheDocument()
    })
  })
})
