import { useEffect, useRef } from 'react'
import styles from './CellTooltip.module.css'
import type { Cell } from './types'

interface CellTooltipProps {
  cell: Cell
  pos: { x: number; y: number }
  pinned: boolean
  onClose: () => void
}

export default function CellTooltip({ cell, pos, pinned, onClose }: CellTooltipProps) {
  const hasLowConfidence = cell.members.some((m) => m.low_confidence)
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (pinned) closeRef.current?.focus()
  }, [pinned])

  return (
    <div
      role={pinned ? 'dialog' : 'tooltip'}
      aria-modal={pinned ? false : undefined}
      aria-label={pinned ? 'Cell members' : undefined}
      className={styles.tooltip}
      style={{ left: pos.x + 12, top: pos.y + 12 }}
    >
      <div className={styles.header}>
        <span className={styles.party}>{cell.dominant_party ?? 'Empty'}</span>
        {pinned && (
          <button
            ref={closeRef}
            type="button"
            aria-label="Close tooltip"
            className={styles.close}
            onClick={onClose}
          >
            ×
          </button>
        )}
      </div>

      {cell.members.length === 0 ? (
        <p className={styles.empty}>No members in this cell.</p>
      ) : (
        <>
          <ul className={styles.members}>
            {cell.members.map((m) => (
              <li key={m.intressent_id} className={m.low_confidence ? styles.lowConfidence : ''}>
                {m.namn} <span className={styles.partyTag}>({m.parti})</span>
                {m.low_confidence && (
                  <>
                    <span aria-hidden="true"> *</span>
                    <span className={styles.srOnly}> (few votes recorded)</span>
                  </>
                )}
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
