import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HexGrid from './HexGrid'
import { NEUTRAL } from './colorMap'
import type { GridData } from './types'

const PARTY_COLORS = { S: '#E8112d', M: '#52BDEC' }

function makeGrid(width: number, height: number, cells: GridData['cells'] = []): GridData {
  return { grid: { width, height }, party_colors: PARTY_COLORS, cells }
}

const GRID_2X2 = makeGrid(2, 2, [
  {
    row: 0, col: 0, dominant_party: 'S',
    members: [{ intressent_id: '1', namn: 'Anna', parti: 'S', low_confidence: false, metadata: { kon: 'kvinna', fodd_ar: 1980, vote_count: 200 } }],
  },
  { row: 0, col: 1, dominant_party: null, members: [] },
  { row: 1, col: 0, dominant_party: 'M',
    members: [{ intressent_id: '2', namn: 'Björn', parti: 'M', low_confidence: false, metadata: { kon: 'man', fodd_ar: 1975, vote_count: 150 } }],
  },
  { row: 1, col: 1, dominant_party: null, members: [] },
])

describe('HexGrid', () => {
  it('renders width × height hex polygons', () => {
    const { container } = render(<HexGrid data={GRID_2X2} colorMode="party" />)
    expect(container.querySelectorAll('polygon')).toHaveLength(4)
  })

  it('renders correct polygon count for 3×2 grid', () => {
    const data = makeGrid(3, 2)
    const { container } = render(<HexGrid data={data} colorMode="party" />)
    expect(container.querySelectorAll('polygon')).toHaveLength(6)
  })

  it('fills a party cell with the party color', () => {
    const { container } = render(<HexGrid data={GRID_2X2} colorMode="party" />)
    const cell = container.querySelector('[data-testid="cell-0-0"]')
    expect(cell).toHaveAttribute('fill', '#E8112d')
  })

  it('fills an empty cell with the neutral color', () => {
    const { container } = render(<HexGrid data={GRID_2X2} colorMode="party" />)
    const emptyCell = container.querySelector('[data-testid="cell-0-1"]')
    expect(emptyCell).toHaveAttribute('fill', NEUTRAL)
  })

  it('applies a different fill in gender mode', () => {
    const { container: partyContainer } = render(<HexGrid data={GRID_2X2} colorMode="party" />)
    const { container: genderContainer } = render(<HexGrid data={GRID_2X2} colorMode="gender" />)
    const partyFill = partyContainer.querySelector('[data-testid="cell-0-0"]')?.getAttribute('fill')
    const genderFill = genderContainer.querySelector('[data-testid="cell-0-0"]')?.getAttribute('fill')
    expect(partyFill).not.toBe(genderFill)
  })

  it('renders inside an SVG element', () => {
    const { container } = render(<HexGrid data={GRID_2X2} colorMode="party" />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('shows a pinned dialog with member name when a cell is clicked', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/Anna/)).toBeInTheDocument()
  })

  it('focuses the close button when the pinned dialog opens', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('button', { name: /close/i })).toHaveFocus()
  })

  it('opens the pinned dialog when pressing Enter on a focused cell', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    screen.getByRole('button', { name: /Anna/ }).focus()
    await userEvent.keyboard('{Enter}')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('does not reopen the dialog when Enter is held down', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    screen.getByRole('button', { name: /Anna/ }).focus()
    await userEvent.keyboard('{Enter>3/}')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('dismisses the dialog when Escape is pressed', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('returns focus to the cell when the dialog is dismissed with Escape', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    const cell = screen.getByRole('button', { name: /Anna/ })
    await userEvent.click(cell)
    await userEvent.keyboard('{Escape}')
    expect(cell).toHaveFocus()
  })

  it('dismisses the dialog when clicking outside the grid', async () => {
    render(
      <div>
        <HexGrid data={GRID_2X2} colorMode="party" />
        <button type="button">Outside</button>
      </div>,
    )
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /outside/i }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows an ephemeral tooltip when hovering a cell', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    await userEvent.hover(screen.getByRole('button', { name: /Anna/ }))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
  })

  it('dismisses the tooltip when the mouse leaves the cell', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    const cell = screen.getByRole('button', { name: /Anna/ })
    await userEvent.hover(cell)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    await userEvent.unhover(cell)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('keeps the pinned dialog visible when the mouse leaves after a click', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    const cell = screen.getByRole('button', { name: /Anna/ })
    await userEvent.click(cell)
    await userEvent.unhover(cell)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('single-row grid has a narrower viewBox than a two-row grid of the same width', () => {
    const { container: one } = render(<HexGrid data={makeGrid(3, 1)} colorMode="party" />)
    const { container: two } = render(<HexGrid data={makeGrid(3, 2)} colorMode="party" />)
    const widthOf = (c: Element) =>
      parseFloat(c.querySelector('svg')!.getAttribute('viewBox')!.split(' ')[2])
    expect(widthOf(one)).toBeLessThan(widthOf(two))
  })
})
