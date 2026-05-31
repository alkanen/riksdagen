import type React from 'react'
import { useEffect, useRef, useState } from 'react'
import CellTooltip from './CellTooltip'
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

type Pos = { x: number; y: number }
type TooltipState = { cell: Cell; pos: Pos; pinned: boolean } | null

interface HexCellProps {
  cell: Cell
  fill: string
  onHover: (cell: Cell, pos: Pos) => void
  onHoverEnd: () => void
  onClick: (cell: Cell, pos: Pos) => void
}

function HexCell({ cell, fill, onHover, onHoverEnd, onClick }: HexCellProps) {
  const [cx, cy] = cellCenter(cell.col, cell.row)
  const ref = useRef<SVGGElement>(null)

  function posFromRect(): Pos {
    const rect = ref.current?.getBoundingClientRect()
    return rect ? { x: rect.left + rect.width / 2, y: rect.bottom } : { x: 0, y: 0 }
  }

  function handleClick(e: React.MouseEvent) {
    onClick(cell, { x: e.clientX, y: e.clientY })
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onClick(cell, posFromRect())
    }
  }

  function handleMouseEnter(e: React.MouseEvent) {
    onHover(cell, { x: e.clientX, y: e.clientY })
  }

  const label =
    cell.members.length === 0
      ? `Empty cell at row ${cell.row}, column ${cell.col}`
      : `${cell.members.map((m) => m.namn).join(', ')} — cell ${cell.row},${cell.col}`

  return (
    <g
      ref={ref}
      tabIndex={0}
      role="button"
      aria-label={label}
      className={styles.cellGroup}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={onHoverEnd}
    >
      <polygon
        data-testid={`cell-${cell.row}-${cell.col}`}
        points={hexPoints(cx, cy)}
        fill={fill}
        className={styles.cell}
      />
    </g>
  )
}

interface HexGridProps {
  data: GridData
  colorMode: ColorMode
}

export default function HexGrid({ data, colorMode }: HexGridProps) {
  const [tooltip, setTooltip] = useState<TooltipState>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const colorOf = buildColorMap(data, colorMode)
  const { width, height } = data.grid

  const cellMap = new Map(data.cells.map((c) => [`${c.row}:${c.col}`, c]))
  const cells: Cell[] = []
  for (let row = 0; row < height; row++) {
    for (let col = 0; col < width; col++) {
      cells.push(cellMap.get(`${row}:${col}`) ?? { row, col, dominant_party: null, members: [] })
    }
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setTooltip(null)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    function onMouseDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setTooltip(null)
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [])

  function handleHover(cell: Cell, pos: Pos) {
    setTooltip((prev) => (prev?.pinned ? prev : { cell, pos, pinned: false }))
  }

  function handleHoverEnd() {
    setTooltip((prev) => (prev?.pinned ? prev : null))
  }

  function handleClick(cell: Cell, pos: Pos) {
    setTooltip({ cell, pos, pinned: true })
  }

  return (
    <div ref={containerRef} className={styles.wrapper}>
      <svg
        viewBox={svgViewBox(width, height)}
        className={styles.grid}
        role="group"
        aria-label="Parliament member voting similarity grid"
      >
        {cells.map((cell) => (
          <HexCell
            key={`${cell.row}:${cell.col}`}
            cell={cell}
            fill={colorOf(cell)}
            onHover={handleHover}
            onHoverEnd={handleHoverEnd}
            onClick={handleClick}
          />
        ))}
      </svg>
      {tooltip !== null && (
        <CellTooltip cell={tooltip.cell} pos={tooltip.pos} onClose={() => setTooltip(null)} />
      )}
    </div>
  )
}
