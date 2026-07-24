import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import CombatUI from '../../components/CombatUI'
import type { Character } from '../../api'

const mockCharacter: Character = {
  id: 1,
  name: 'Test Hero',
  character_class: 'Wanderer',
  background: 'A test backstory',
  stats: { strength: 5, intellect: 5, charm: 5 },
  show_tutorials: true,
}

describe('CombatUI', () => {
  it('renders null when worldState is null', () => {
    const { container } = render(
      <CombatUI worldState={null} character={mockCharacter} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders null when combat is not active', () => {
    const { container } = render(
      <CombatUI worldState={{ is_combat_active: false }} character={mockCharacter} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders null when player_stats or active_npcs are missing', () => {
    const { container } = render(
      <CombatUI
        worldState={{ is_combat_active: true, player_stats: null, active_npcs: null }}
        character={mockCharacter}
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders combat HUD when combat is active with valid data', () => {
    const worldState = {
      is_combat_active: true,
      player_stats: { hp: 80, steam: 50, max_steam: 100 },
      active_npcs: [
        { id: 'npc_1', name: 'Iron Golem', hp: 60, max_hp: 100, status_effects: [] },
      ],
    }
    render(<CombatUI worldState={worldState} character={mockCharacter} />)
    
    // Player HP displayed
    expect(screen.getByText('80')).toBeInTheDocument()
    // Steam label
    expect(screen.getByText('Steam')).toBeInTheDocument()
    // Vitality label
    expect(screen.getByText('Vitality')).toBeInTheDocument()
  })

  it('displays enemy name and HP ratio', () => {
    const worldState = {
      is_combat_active: true,
      player_stats: { hp: 100, steam: 75, max_steam: 100 },
      active_npcs: [
        { id: 'npc_1', name: 'Rogue Automata', hp: 45, max_hp: 100, status_effects: [] },
      ],
    }
    render(<CombatUI worldState={worldState} character={mockCharacter} />)
    
    expect(screen.getByText('Rogue Automata')).toBeInTheDocument()
    expect(screen.getByText('45/100')).toBeInTheDocument()
  })

  it('displays enemy status effects when present', () => {
    const worldState = {
      is_combat_active: true,
      player_stats: { hp: 100, steam: 50, max_steam: 100 },
      active_npcs: [
        { id: 'npc_1', name: 'Guard', hp: 80, max_hp: 100, status_effects: ['Stunned', 'Burning'] },
      ],
    }
    render(<CombatUI worldState={worldState} character={mockCharacter} />)
    
    expect(screen.getByText('Stunned')).toBeInTheDocument()
    expect(screen.getByText('Burning')).toBeInTheDocument()
  })

  it('renders multiple enemies', () => {
    const worldState = {
      is_combat_active: true,
      player_stats: { hp: 90, steam: 60, max_steam: 100 },
      active_npcs: [
        { id: 'npc_1', name: 'Bandit A', hp: 30, max_hp: 50 },
        { id: 'npc_2', name: 'Bandit B', hp: 50, max_hp: 50 },
      ],
    }
    render(<CombatUI worldState={worldState} character={mockCharacter} />)
    
    expect(screen.getByText('Bandit A')).toBeInTheDocument()
    expect(screen.getByText('Bandit B')).toBeInTheDocument()
    expect(screen.getByText('30/50')).toBeInTheDocument()
    expect(screen.getByText('50/50')).toBeInTheDocument()
  })

  it('shows tutorial box when tutorials are enabled', () => {
    const worldState = {
      is_combat_active: true,
      player_stats: { hp: 100, steam: 100, max_steam: 100 },
      active_npcs: [{ id: 'npc_1', name: 'Enemy', hp: 50, max_hp: 100 }],
    }
    render(<CombatUI worldState={worldState} character={mockCharacter} />)
    
    expect(screen.getByText(/Combat HUD/)).toBeInTheDocument()
  })

  it('hides tutorial box when tutorials are disabled', () => {
    const worldState = {
      is_combat_active: true,
      player_stats: { hp: 100, steam: 100, max_steam: 100 },
      active_npcs: [{ id: 'npc_1', name: 'Enemy', hp: 50, max_hp: 100 }],
    }
    const charNoTutorials = { ...mockCharacter, show_tutorials: false }
    render(<CombatUI worldState={worldState} character={charNoTutorials} />)
    
    expect(screen.queryByText(/Combat HUD/)).not.toBeInTheDocument()
  })
})
