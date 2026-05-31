import { useState } from 'react'
import styles from './App.module.css'
import ColorByToggle from './ColorByToggle'
import HexGrid from './HexGrid'
import type { ColorMode } from './types'
import { useGridData } from './useGridData'

export default function App() {
  const state = useGridData()
  const [colorMode, setColorMode] = useState<ColorMode>('party')

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <h1 className={styles.title}>Riksdagen</h1>
        <ColorByToggle value={colorMode} onChange={setColorMode} />
      </header>

      <main className={styles.main}>
        {state.status === 'loading' && (
          <p className={styles.status}>Loading grid data…</p>
        )}
        {state.status === 'error' && (
          <p className={styles.status}>Failed to load data: {state.message}</p>
        )}
        {state.status === 'ready' && (
          <div className={styles.gridWrapper}>
            <HexGrid data={state.data} colorMode={colorMode} />
          </div>
        )}
      </main>
    </div>
  )
}
