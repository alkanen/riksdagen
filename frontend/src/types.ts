export interface MemberMetadata {
  kon: string
  fodd_ar: number
  vote_count: number
  [key: string]: unknown
}

export interface Member {
  intressent_id: string
  namn: string
  parti: string
  low_confidence: boolean
  metadata: MemberMetadata
}

export interface Cell {
  row: number
  col: number
  dominant_party: string | null
  members: Member[]
}

export interface GridData {
  grid: { width: number; height: number }
  party_colors: Record<string, string>
  cells: Cell[]
}

export type ColorMode = 'party' | 'gender' | 'age' | 'votes'
