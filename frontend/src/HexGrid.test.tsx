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

  it('shows a tooltip with member name when a cell is clicked', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    expect(screen.getByText(/Anna/)).toBeInTheDocument()
  })

  it('dismisses the tooltip when Escape is pressed', async () => {
    render(<HexGrid data={GRID_2X2} colorMode="party" />)
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('dismisses the tooltip when clicking outside the grid', async () => {
    render(
      <div>
        <HexGrid data={GRID_2X2} colorMode="party" />
        <button type="button">Outside</button>
      </div>,
    )
    await userEvent.click(screen.getByTestId('cell-0-0'))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /outside/i }))
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('single-row grid has a narrower viewBox than a two-row grid of the same width', () => {
    const { container: one } = render(<HexGrid data={makeGrid(3, 1)} colorMode="party" />)
    const { container: two } = render(<HexGrid data={makeGrid(3, 2)} colorMode="party" />)
    const widthOf = (c: Element) =>
      parseFloat(c.querySelector('svg')!.getAttribute('viewBox')!.split(' ')[2])
    expect(widthOf(one)).toBeLessThan(widthOf(two))
  })
})
