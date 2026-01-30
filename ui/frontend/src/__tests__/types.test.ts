import { describe, it, expect } from 'vitest'
import { getProcessStatus, type StatusResponse } from '../types'

describe('getProcessStatus', () => {
  const createStatusResponse = (
    overrides: Partial<StatusResponse> = {}
  ): StatusResponse => ({
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

  it('should return "stopped" when not running', () => {
    /**
     * GIVEN a status response with running=false
     * WHEN getProcessStatus is called
     * THEN should return "stopped"
     */
    const status = createStatusResponse({ running: false })
    expect(getProcessStatus(status)).toBe('stopped')
  })

  it('should return "running" when running and not paused', () => {
    /**
     * GIVEN a status response with running=true
     * WHEN getProcessStatus is called
     * THEN should return "running"
     */
    const status = createStatusResponse({ running: true, paused: false })
    expect(getProcessStatus(status)).toBe('running')
  })

  it('should return "paused" when paused', () => {
    /**
     * GIVEN a status response with paused=true
     * WHEN getProcessStatus is called
     * THEN should return "paused"
     */
    const status = createStatusResponse({ running: true, paused: true })
    expect(getProcessStatus(status)).toBe('paused')
  })

  it('should return "rate_limited" when rate_limited_until is set', () => {
    /**
     * GIVEN a status response with rate_limited_until set
     * WHEN getProcessStatus is called
     * THEN should return "rate_limited" (takes priority)
     */
    const status = createStatusResponse({
      running: true,
      rate_limited_until: '2024-01-15T10:00:00',
    })
    expect(getProcessStatus(status)).toBe('rate_limited')
  })

  it('should prioritize rate_limited over paused', () => {
    /**
     * GIVEN a status response with both rate_limited and paused
     * WHEN getProcessStatus is called
     * THEN should return "rate_limited"
     */
    const status = createStatusResponse({
      running: true,
      paused: true,
      rate_limited_until: '2024-01-15T10:00:00',
    })
    expect(getProcessStatus(status)).toBe('rate_limited')
  })

  it('should prioritize paused over running', () => {
    /**
     * GIVEN a status response with both running and paused
     * WHEN getProcessStatus is called
     * THEN should return "paused"
     */
    const status = createStatusResponse({
      running: true,
      paused: true,
    })
    expect(getProcessStatus(status)).toBe('paused')
  })
})
