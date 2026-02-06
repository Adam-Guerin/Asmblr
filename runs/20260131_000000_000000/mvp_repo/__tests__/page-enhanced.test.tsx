import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Page from '../app/page'

// Mock the loading components
jest.mock('../components/ui/loading', () => ({
  LoadingSpinner: ({ size }: { size: string }) => <div data-testid="loading-spinner" data-size={size} />,
  Skeleton: ({ className }: { className: string }) => <div data-testid="skeleton" className={className} />,
}))

describe('Page Component', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('shows loading state initially', () => {
    render(<Page />)
    
    expect(screen.getAllByTestId('skeleton')).toHaveLength(8)
    expect(screen.queryByText('Prototype launched')).not.toBeInTheDocument()
  })

  it('renders content after loading', async () => {
    render(<Page />)
    
    // Fast-forward past loading
    jest.advanceTimersByTime(1500)
    
    await waitFor(() => {
      expect(screen.getByText('Prototype launched')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Flows')).toBeInTheDocument()
    expect(screen.getByText('3 ready')).toBeInTheDocument()
    expect(screen.getByText('Stack highlights')).toBeInTheDocument()
  })

  it('displays error state when loading fails', async () => {
    // Mock setTimeout to reject
    jest.spyOn(global, 'setTimeout').mockImplementation((cb) => {
      if (typeof cb === 'function') {
        cb(() => Promise.reject(new Error('Network error')))
      }
      return 1 as any
    })

    render(<Page />)
    
    await waitFor(() => {
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      expect(screen.getByText('Failed to load metrics')).toBeInTheDocument()
    })
  })

  it('has working buttons after loading', async () => {
    const user = userEvent.setup()
    render(<Page />)
    
    jest.advanceTimersByTime(1500)
    
    await waitFor(() => {
      expect(screen.getByText('Launch prototype')).toBeInTheDocument()
      expect(screen.getByText('View docs')).toBeInTheDocument()
    })
    
    const launchButton = screen.getByText('Launch prototype')
    await user.click(launchButton)
    
    // Button should be clickable (no error thrown)
    expect(launchButton).toBeInTheDocument()
  })

  it('shows metrics cards correctly', async () => {
    render(<Page />)
    
    jest.advanceTimersByTime(1500)
    
    await waitFor(() => {
      expect(screen.getByText('Flows')).toBeInTheDocument()
      expect(screen.getByText('3 ready')).toBeInTheDocument()
      expect(screen.getByText('API')).toBeInTheDocument()
      expect(screen.getByText('status + data')).toBeInTheDocument()
      expect(screen.getByText('Focus')).toBeInTheDocument()
      expect(screen.getByText('Prototype built')).toBeInTheDocument()
    })
  })
})
