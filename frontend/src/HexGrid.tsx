import { buildColorMap } from './colorMap'
import styles from './HexGrid.module.css'
import type { Cell, ColorMode, GridData } from './types'

const HEX_SIZE = 28
const HEX_W = Math.sqrt(3) * HEX_SIZE
const PAD = 4

function hexPoints(cx: number, cy: number): string {
  return Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i + Math.PI / 6
    return `${(cx + HEX_SIZE * Math.cos(angle)).toFixed(2)},${(cy + HEX_SIZE * Math.sin(angle)).toFixed(2)}`
  }).join(' ')
}

function cellCenter(col: number, row: number): [number, number] {
  const x = PAD + HEX_W / 2 + col * HEX_W + (row % 2 === 1 ? HEX_W / 2 : 0)
  const y = PAD + HEX_SIZE + row * HEX_SIZE * 1.5
  return [x, y]
}

function svgViewBox(width: number, height: number): string {
  const hasOddRow = height >= 2
  const w = 2 * PAD + width * HEX_W + (hasOddRow ? HEX_W / 2 : 0)
  const h = 2 * PAD + 2 * HEX_SIZE + Math.max(height - 1, 0) * HEX_SIZE * 1.5
  return `0 0 ${w.toFixed(2)} ${h.toFixed(2)}`
}

interface HexCellProps {
  cell: Cell
  fill: string
}

function HexCell({ cell, fill }: HexCellProps) {
  const [cx, cy] = cellCenter(cell.col, cell.row)
  return (
    <polygon
      data-testid={`cell-${cell.row}-${cell.col}`}
      points={hexPoints(cx, cy)}
      fill={fill}
      className={styles.cell}
    />
  )
}

interface HexGridProps {
  data: GridData
  colorMode: ColorMode
}

export default function HexGrid({ data, colorMode }: HexGridProps) {
  const colorOf = buildColorMap(data, colorMode)
  const { width, height } = data.grid

  const cellMap = new Map(data.cells.map((c) => [`${c.row}:${c.col}`, c]))

  const cells: Cell[] = []
  for (let row = 0; row < height; row++) {
    for (let col = 0; col < width; col++) {
      cells.push(cellMap.get(`${row}:${col}`) ?? { row, col, dominant_party: null, members: [] })
    }
  }

  return (
    <svg
      viewBox={svgViewBox(width, height)}
      className={styles.grid}
      role="img"
      aria-label="Parliament member voting similarity grid"
    >
      {cells.map((cell) => (
        <HexCell key={`${cell.row}:${cell.col}`} cell={cell} fill={colorOf(cell)} />
      ))}
    </svg>
  )
}
