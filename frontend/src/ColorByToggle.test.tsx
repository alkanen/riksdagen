import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ColorByToggle from './ColorByToggle'
import type { ColorMode } from './types'

describe('ColorByToggle', () => {
  it('renders all four mode options', () => {
    render(<ColorByToggle value="party" onChange={() => {}} />)
    expect(screen.getByRole('button', { name: /party/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /gender/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /age/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /votes/i })).toBeInTheDocument()
  })

  it('marks the active mode button as pressed', () => {
    render(<ColorByToggle value="gender" onChange={() => {}} />)
    expect(screen.getByRole('button', { name: /gender/i })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /party/i })).toHaveAttribute('aria-pressed', 'false')
  })

  it('calls onChange with the correct mode when a button is clicked', async () => {
    const onChange = vi.fn<(mode: ColorMode) => void>()
    render(<ColorByToggle value="party" onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: /age/i }))
    expect(onChange).toHaveBeenCalledWith('age')
  })

  it('does not call onChange when the active mode is clicked again', async () => {
    const onChange = vi.fn<(mode: ColorMode) => void>()
    render(<ColorByToggle value="party" onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: /party/i }))
    expect(onChange).not.toHaveBeenCalled()
  })
})
