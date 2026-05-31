import { buildColorMap, NEUTRAL } from './colorMap'
import type { Cell, GridData } from './types'

function makeCell(
  row: number,
  col: number,
  dominant_party: string | null,
  members: Cell['members'] = [],
): Cell {
  return { row, col, dominant_party, members }
}

function makeMember(parti: string, kon: string, fodd_ar: number, vote_count: number): Cell['members'][number] {
  return {
    intressent_id: `id-${parti}-${fodd_ar}-${kon}`,
    namn: 'Test Person',
    parti,
    low_confidence: false,
    metadata: { kon, fodd_ar, vote_count },
  }
}

const PARTY_COLORS = { S: '#E8112d', M: '#52BDEC' }

const EMPTY_GRID: GridData = {
  grid: { width: 2, height: 2 },
  party_colors: PARTY_COLORS,
  cells: [],
}

describe('buildColorMap — party mode', () => {
  it('returns party color for a cell with dominant party', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'party')
    const cell = makeCell(0, 0, 'S', [makeMember('S', 'kvinna', 1980, 200)])
    expect(colorOf(cell)).toBe('#E8112d')
  })

  it('returns neutral for an empty cell', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'party')
    expect(colorOf(makeCell(0, 0, null))).toBe(NEUTRAL)
  })

  it('returns neutral for unknown party', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'party')
    const cell = makeCell(0, 0, 'XY', [makeMember('XY', 'man', 1975, 100)])
    expect(colorOf(cell)).toBe(NEUTRAL)
  })
})

describe('buildColorMap — gender mode', () => {
  it('returns a non-neutral color for a cell with members', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'gender')
    const cell = makeCell(0, 0, 'S', [makeMember('S', 'kvinna', 1980, 200)])
    expect(colorOf(cell)).not.toBe(NEUTRAL)
  })

  it('returns neutral for an empty cell', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'gender')
    expect(colorOf(makeCell(0, 0, null))).toBe(NEUTRAL)
  })

  it('returns different colors for majority-women vs majority-men cells', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'gender')
    const womenCell = makeCell(0, 0, 'S', [
      makeMember('S', 'kvinna', 1980, 200),
      makeMember('S', 'kvinna', 1982, 200),
    ])
    const menCell = makeCell(1, 0, 'M', [
      makeMember('M', 'man', 1978, 150),
      makeMember('M', 'man', 1975, 180),
    ])
    expect(colorOf(womenCell)).not.toBe(colorOf(menCell))
  })
})

describe('buildColorMap — age mode', () => {
  it('returns a non-neutral color for a cell with members', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'age')
    const cell = makeCell(0, 0, 'S', [makeMember('S', 'kvinna', 1985, 200)])
    expect(colorOf(cell)).not.toBe(NEUTRAL)
  })

  it('returns neutral for an empty cell', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'age')
    expect(colorOf(makeCell(0, 0, null))).toBe(NEUTRAL)
  })

  it('returns different colors for very young vs very old cohorts', () => {
    const colorOf = buildColorMap(EMPTY_GRID, 'age')
    const youngCell = makeCell(0, 0, 'S', [makeMember('S', 'kvinna', 1995, 100)])
    const oldCell = makeCell(1, 0, 'M', [makeMember('M', 'man', 1945, 300)])
    expect(colorOf(youngCell)).not.toBe(colorOf(oldCell))
  })
})

describe('buildColorMap — votes mode', () => {
  const gridWithVotes: GridData = {
    grid: { width: 2, height: 2 },
    party_colors: PARTY_COLORS,
    cells: [
      makeCell(0, 0, 'S', [makeMember('S', 'kvinna', 1980, 50)]),
      makeCell(0, 1, 'M', [makeMember('M', 'man', 1975, 150)]),
      makeCell(1, 0, 'S', [makeMember('S', 'kvinna', 1985, 250)]),
      makeCell(1, 1, 'M', [makeMember('M', 'man', 1970, 350)]),
    ],
  }

  it('returns a non-neutral color for a cell with members', () => {
    const colorOf = buildColorMap(gridWithVotes, 'votes')
    expect(colorOf(gridWithVotes.cells[0])).not.toBe(NEUTRAL)
  })

  it('returns neutral for an empty cell', () => {
    const colorOf = buildColorMap(gridWithVotes, 'votes')
    expect(colorOf(makeCell(2, 2, null))).toBe(NEUTRAL)
  })

  it('returns different colors for low vs high vote count cells', () => {
    const colorOf = buildColorMap(gridWithVotes, 'votes')
    expect(colorOf(gridWithVotes.cells[0])).not.toBe(colorOf(gridWithVotes.cells[3]))
  })
})
