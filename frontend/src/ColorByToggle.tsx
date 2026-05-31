import styles from './ColorByToggle.module.css'
import type { ColorMode } from './types'

const MODES: { value: ColorMode; label: string }[] = [
  { value: 'party', label: 'Party' },
  { value: 'gender', label: 'Gender' },
  { value: 'age', label: 'Age cohort' },
  { value: 'votes', label: 'Votes' },
]

interface ColorByToggleProps {
  value: ColorMode
  onChange: (mode: ColorMode) => void
}

export default function ColorByToggle({ value, onChange }: ColorByToggleProps) {
  return (
    <div className={styles.toggle} role="group" aria-label="Color by">
      {MODES.map((mode) => (
        <button
          key={mode.value}
          type="button"
          className={`${styles.button} ${value === mode.value ? styles.active : ''}`}
          aria-pressed={value === mode.value}
          onClick={() => {
            if (value !== mode.value) onChange(mode.value)
          }}
        >
          {mode.label}
        </button>
      ))}
    </div>
  )
}
