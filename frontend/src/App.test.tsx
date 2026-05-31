import { render, screen } from '@testing-library/react'
import App from './App'

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('renders the page title', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Riksdagen')
  })

  it('renders all four color-by toggle options', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /party/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /gender/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /age/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /votes/i })).toBeInTheDocument()
  })

  it('shows a loading indicator on mount', () => {
    render(<App />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })
})
