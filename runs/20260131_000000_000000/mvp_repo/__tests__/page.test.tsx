import { render, screen } from '@testing-library/react'
import Page from '../app/page'

describe('Page', () => {
  it('renders Audit MVP heading', () => {
    render(<Page />)
    const heading = screen.getByText('Prototype launched')
    expect(heading).toBeInTheDocument()
  })

  it('renders metrics cards', () => {
    render(<Page />)
    expect(screen.getByText('Flows')).toBeInTheDocument()
    expect(screen.getByText('3 ready')).toBeInTheDocument()
    expect(screen.getByText('API')).toBeInTheDocument()
    expect(screen.getByText('status + data')).toBeInTheDocument()
  })

  it('renders stack highlights', () => {
    render(<Page />)
    expect(screen.getByText('Stack highlights')).toBeInTheDocument()
    expect(screen.getByText('Prototype ready for fast validation')).toBeInTheDocument()
  })

  it('has working buttons', () => {
    render(<Page />)
    const launchButton = screen.getByText('Launch prototype')
    const docsButton = screen.getByText('View docs')
    expect(launchButton).toBeInTheDocument()
    expect(docsButton).toBeInTheDocument()
  })
})
