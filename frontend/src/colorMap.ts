import type { Cell, ColorMode, GridData } from './types'

export const NEUTRAL = '#1e2030'

const GENDER_COLORS: Record<string, string> = {
  kvinna: '#c084fc',
  man: '#60a5fa',
}

const AGE_COLORS = ['#fbbf24', '#fb923c', '#f87171', '#94a3b8'] as const

const VOTE_COLORS = ['#bfdbfe', '#60a5fa', '#2563eb', '#1e3a8a'] as const

function dominantKey(values: string[]): string | null {
  if (values.length === 0) return null
  const counts: Record<string, number> = {}
  for (const v of values) counts[v] = (counts[v] ?? 0) + 1
  return Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0][0]
}

function ageBucket(avgYear: number): number {
  if (avgYear >= 1985) return 0
  if (avgYear >= 1975) return 1
  if (avgYear >= 1965) return 2
  return 3
}

function voteBucket(avg: number, q1: number, q2: number, q3: number): number {
  if (avg < q1) return 0
  if (avg < q2) return 1
  if (avg < q3) return 2
  return 3
}

export function buildColorMap(data: GridData, mode: ColorMode): (cell: Cell) => string {
  if (mode === 'party') {
    return (cell) => {
      if (cell.members.length === 0 || cell.dominant_party === null) return NEUTRAL
      return data.party_colors[cell.dominant_party] ?? NEUTRAL
    }
  }

  if (mode === 'gender') {
    return (cell) => {
      if (cell.members.length === 0) return NEUTRAL
      const dominant = dominantKey(cell.members.map((m) => m.metadata.kon))
      return dominant !== null ? (GENDER_COLORS[dominant] ?? NEUTRAL) : NEUTRAL
    }
  }

  if (mode === 'age') {
    return (cell) => {
      if (cell.members.length === 0) return NEUTRAL
      const years = cell.members.map((m) => m.metadata.fodd_ar).filter((y) => typeof y === 'number')
      if (years.length === 0) return NEUTRAL
      const avg = years.reduce((a, b) => a + b, 0) / years.length
      return AGE_COLORS[ageBucket(avg)]
    }
  }

  // votes mode — compute quartile thresholds across all populated cells
  const activeCells = data.cells.filter((c) => c.members.length > 0)
  const avgs = activeCells
    .map((c) => c.members.reduce((a, m) => a + m.metadata.vote_count, 0) / c.members.length)
    .sort((a, b) => a - b)

  const at = (p: number) => avgs[Math.floor(p * (avgs.length - 1))] ?? 0
  const q1 = at(0.25)
  const q2 = at(0.5)
  const q3 = at(0.75)

  return (cell) => {
    if (cell.members.length === 0) return NEUTRAL
    const avg = cell.members.reduce((a, m) => a + m.metadata.vote_count, 0) / cell.members.length
    return VOTE_COLORS[voteBucket(avg, q1, q2, q3)]
  }
}
