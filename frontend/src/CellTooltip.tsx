import styles from './CellTooltip.module.css'
import type { Cell } from './types'

interface CellTooltipProps {
  cell: Cell
  pos: { x: number; y: number }
  onClose: () => void
}

export default function CellTooltip({ cell, pos, onClose }: CellTooltipProps) {
  const hasLowConfidence = cell.members.some((m) => m.low_confidence)

  return (
    <div
      role="tooltip"
      className={styles.tooltip}
      style={{ left: pos.x + 12, top: pos.y + 12 }}
    >
      <div className={styles.header}>
        <span className={styles.party}>{cell.dominant_party ?? 'Empty'}</span>
        <button type="button" aria-label="Close tooltip" className={styles.close} onClick={onClose}>
          ×
        </button>
      </div>

      {cell.members.length === 0 ? (
        <p className={styles.empty}>No members in this cell.</p>
      ) : (
        <>
          <ul className={styles.members}>
            {cell.members.map((m) => (
              <li key={m.intressent_id} className={m.low_confidence ? styles.lowConfidence : ''}>
                {m.namn} <span className={styles.partyTag}>({m.parti})</span>
                {m.low_confidence && <span aria-hidden="true"> *</span>}
              </li>
            ))}
          </ul>
          {hasLowConfidence && (
            <p className={styles.legend}>* Fewer votes than confidence threshold</p>
          )}
        </>
      )}
    </div>
  )
}
