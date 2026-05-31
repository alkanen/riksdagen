import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CellTooltip from './CellTooltip'
import type { Cell } from './types'

const POS = { x: 100, y: 100 }

function makeCell(overrides: Partial<Cell> = {}): Cell {
  return {
    row: 0,
    col: 0,
    dominant_party: 'S',
    members: [
      {
        intressent_id: '1',
        namn: 'Anna Svensson',
        parti: 'S',
        low_confidence: false,
        metadata: { kon: 'kvinna', fodd_ar: 1980, vote_count: 200 },
      },
    ],
    ...overrides,
  }
}

describe('CellTooltip', () => {
  it('shows member name and party abbreviation', () => {
    render(<CellTooltip cell={makeCell()} pos={POS} pinned={true} onClose={() => {}} />)
    expect(screen.getByText(/Anna Svensson/)).toBeInTheDocument()
    expect(screen.getByText(/\(S\)/)).toBeInTheDocument()
  })

  it('shows a low-confidence indicator for flagged members', () => {
    const cell = makeCell({
      members: [
        {
          intressent_id: '2',
          namn: 'Björn',
          parti: 'M',
          low_confidence: true,
          metadata: { kon: 'man', fodd_ar: 1975, vote_count: 10 },
        },
      ],
    })
    render(<CellTooltip cell={cell} pos={POS} pinned={true} onClose={() => {}} />)
    const item = screen.getByText(/Björn/).closest('li')
    expect(item).toHaveTextContent('*')
  })

  it('exposes low-confidence state to screen readers', () => {
    const cell = makeCell({
      members: [
        {
          intressent_id: '2',
          namn: 'Björn',
          parti: 'M',
          low_confidence: true,
          metadata: { kon: 'man', fodd_ar: 1975, vote_count: 10 },
        },
      ],
    })
    render(<CellTooltip cell={cell} pos={POS} pinned={true} onClose={() => {}} />)
    const item = screen.getByText(/Björn/).closest('li')
    expect(item).toHaveTextContent(/few votes recorded/i)
  })

  it('does not show a low-confidence indicator for confident members', () => {
    render(<CellTooltip cell={makeCell()} pos={POS} pinned={true} onClose={() => {}} />)
    const item = screen.getByText(/Anna Svensson/).closest('li')
    expect(item).not.toHaveTextContent('*')
  })

  it('shows a "no members" message for an empty cell', () => {
    const cell = makeCell({ members: [], dominant_party: null })
    render(<CellTooltip cell={cell} pos={POS} pinned={true} onClose={() => {}} />)
    expect(screen.getByText(/no members/i)).toBeInTheDocument()
  })

  it('shows the close button when pinned', () => {
    render(<CellTooltip cell={makeCell()} pos={POS} pinned={true} onClose={() => {}} />)
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
  })

  it('does not show the close button when unpinned', () => {
    render(<CellTooltip cell={makeCell()} pos={POS} pinned={false} onClose={() => {}} />)
    expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
  })

  it('calls onClose when the close button is clicked', async () => {
    const onClose = vi.fn()
    render(<CellTooltip cell={makeCell()} pos={POS} pinned={true} onClose={onClose} />)
    await userEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })
})
