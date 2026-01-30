import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusCards from '../../components/StatusCards'
import type { StatusResponse } from '../../types'

const createMockStatus = (overrides: Partial<StatusResponse> = {}): StatusResponse => ({
  running: false,
  paused: false,
  iteration: null,
  performer: null,
  performer_emoji: null,
  beans_pending: 0,
  beans_completed: 0,
  no_progress_count: 0,
  started_at: null,
  rate_limited_until: null,
  ...overrides,
})

describe('StatusCards', () => {
  describe('loading state', () => {
    it('should show loading skeleton when loading with no data', () => {
      /**
       * GIVEN loading=true and no status data
       * WHEN component is rendered
       * THEN should show loading skeletons
       */
      render(<StatusCards status={null} loading={true} connected={false} />)

      // Should have 4 skeleton cards
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBe(4)
    })

    it('should not show loading skeleton when status data exists', () => {
      /**
       * GIVEN loading=true but status data exists
       * WHEN component is rendered
       * THEN should show actual data, not skeletons
       */
      const status = createMockStatus({ running: true })
      render(<StatusCards status={status} loading={true} connected={true} />)

      // Should show Running label, not skeleton
      expect(screen.getByText('Running')).toBeInTheDocument()
    })
  })

  describe('status badge', () => {
    it('should show "Stopped" when not running', () => {
      /**
       * GIVEN status with running=false
       * WHEN component is rendered
       * THEN should show "Stopped" label
       */
      const status = createMockStatus({ running: false })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('Stopped')).toBeInTheDocument()
    })

    it('should show "Running" when running', () => {
      /**
       * GIVEN status with running=true
       * WHEN component is rendered
       * THEN should show "Running" label
       */
      const status = createMockStatus({ running: true })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('Running')).toBeInTheDocument()
    })

    it('should show "Paused" when paused', () => {
      /**
       * GIVEN status with paused=true
       * WHEN component is rendered
       * THEN should show "Paused" label
       */
      const status = createMockStatus({ running: true, paused: true })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('Paused')).toBeInTheDocument()
    })

    it('should show "Rate Limited" when rate limited', () => {
      /**
       * GIVEN status with rate_limited_until set
       * WHEN component is rendered
       * THEN should show "Rate Limited" label
       */
      const status = createMockStatus({
        running: true,
        rate_limited_until: new Date(Date.now() + 60000).toISOString(),
      })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('Rate Limited')).toBeInTheDocument()
    })
  })

  describe('connection badge', () => {
    it('should show "Connected" when connected', () => {
      /**
       * GIVEN connected=true
       * WHEN component is rendered
       * THEN should show "Connected" text
       */
      const status = createMockStatus()
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('should show "Disconnected" when not connected', () => {
      /**
       * GIVEN connected=false
       * WHEN component is rendered
       * THEN should show "Disconnected" text
       */
      const status = createMockStatus()
      render(<StatusCards status={status} loading={false} connected={false} />)

      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  describe('status cards', () => {
    it('should display iteration number', () => {
      /**
       * GIVEN status with iteration=5
       * WHEN component is rendered
       * THEN should display the iteration number
       */
      const status = createMockStatus({ iteration: 5 })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('Iteration')).toBeInTheDocument()
    })

    it('should display "-" when iteration is null', () => {
      /**
       * GIVEN status with iteration=null
       * WHEN component is rendered
       * THEN should display "-"
       */
      const status = createMockStatus({ iteration: null })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('-')).toBeInTheDocument()
    })

    it('should display performer with emoji', () => {
      /**
       * GIVEN status with performer and emoji
       * WHEN component is rendered
       * THEN should display performer name with emoji
       */
      const status = createMockStatus({ performer: 'task', performer_emoji: '📋' })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('📋 task')).toBeInTheDocument()
    })

    it('should display "None" when no performer', () => {
      /**
       * GIVEN status with no performer
       * WHEN component is rendered
       * THEN should display "None"
       */
      const status = createMockStatus({ performer: null })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('None')).toBeInTheDocument()
    })

    it('should display pending and completed beans count', () => {
      /**
       * GIVEN status with bean counts
       * WHEN component is rendered
       * THEN should display the counts
       */
      const status = createMockStatus({ beans_pending: 5, beans_completed: 10 })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument()
      expect(screen.getByText('Tasks Pending')).toBeInTheDocument()
      expect(screen.getByText('Tasks Done')).toBeInTheDocument()
    })

    it('should display no progress count when present', () => {
      /**
       * GIVEN status with no_progress_count > 0
       * WHEN component is rendered
       * THEN should display the no progress subtitle
       */
      const status = createMockStatus({ no_progress_count: 3 })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText('3 no progress')).toBeInTheDocument()
    })
  })

  describe('rate limited countdown', () => {
    it('should show countdown when rate limited', () => {
      /**
       * GIVEN status with rate_limited_until in the future
       * WHEN component is rendered
       * THEN should show countdown message
       */
      const futureTime = new Date(Date.now() + 5 * 60000).toISOString() // 5 minutes
      const status = createMockStatus({ running: true, rate_limited_until: futureTime })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.getByText(/Rate limited. Resuming in/)).toBeInTheDocument()
    })

    it('should not show countdown when not rate limited', () => {
      /**
       * GIVEN status without rate_limited_until
       * WHEN component is rendered
       * THEN should not show countdown
       */
      const status = createMockStatus({ running: true })
      render(<StatusCards status={status} loading={false} connected={true} />)

      expect(screen.queryByText(/Rate limited/)).not.toBeInTheDocument()
    })
  })
})
