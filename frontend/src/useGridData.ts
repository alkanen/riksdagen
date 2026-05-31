import { useEffect, useState } from 'react'
import type { GridData } from './types'

const DATA_URL = (import.meta.env.VITE_DATA_URL as string | undefined) || '/data.json'

type GridDataState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: GridData }

export function useGridData(): GridDataState {
  const [state, setState] = useState<GridDataState>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    fetch(DATA_URL, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<GridData>
      })
      .then((data) => setState({ status: 'ready', data }))
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === 'AbortError') return
        setState({ status: 'error', message: String(e) })
      })
    return () => controller.abort()
  }, [])

  return state
}
