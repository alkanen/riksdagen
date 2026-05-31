import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the page heading', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Riksdagen'
    )
  })

  it('renders a description', () => {
    render(<App />)
    expect(screen.getByText(/hexagonal grid/i)).toBeInTheDocument()
  })
})
