import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useApi, useStatus, useStart, useStop } from '../../hooks/useApi'
import { mockFetch } from '../setup'

describe('useApi', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('basic functionality', () => {
    it('should initialize with default state', () => {
      /**
       * GIVEN useApi hook is rendered
       * WHEN no API call has been made
       * THEN data should be null, loading false, error null
       */
      const { result } = renderHook(() => useApi<{ message: string }>('/api/test'))

      expect(result.current.data).toBeNull()
      expect(result.current.loading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should set loading to true during fetch', async () => {
      /**
       * GIVEN useApi hook
       * WHEN execute is called
       * THEN loading should be true while waiting
       */
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ message: 'test' }),
        }), 100))
      )

      const { result } = renderHook(() => useApi<{ message: string }>('/api/test'))

      act(() => {
        result.current.execute()
      })

      expect(result.current.loading).toBe(true)

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should set data on successful fetch', async () => {
      /**
       * GIVEN useApi hook and successful API response
       * WHEN execute is called
       * THEN data should be set with response
       */
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'success' }),
      })

      const { result } = renderHook(() => useApi<{ message: string }>('/api/test'))

      await act(async () => {
        await result.current.execute()
      })

      expect(result.current.data).toEqual({ message: 'success' })
      expect(result.current.error).toBeNull()
    })

    it('should set error on failed fetch', async () => {
      /**
       * GIVEN useApi hook and failed API response
       * WHEN execute is called
       * THEN error should be set
       */
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        text: () => Promise.resolve('Internal Server Error'),
      })

      const { result } = renderHook(() => useApi<{ message: string }>('/api/test'))

      await act(async () => {
        await result.current.execute()
      })

      expect(result.current.data).toBeNull()
      expect(result.current.error).toBe('Internal Server Error')
    })

    it('should handle network errors', async () => {
      /**
       * GIVEN useApi hook and network error
       * WHEN execute is called
       * THEN error should be set with error message
       */
      mockFetch.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useApi<{ message: string }>('/api/test'))

      await act(async () => {
        await result.current.execute()
      })

      expect(result.current.error).toBe('Network error')
    })
  })

  describe('callbacks', () => {
    it('should call onSuccess callback on successful fetch', async () => {
      /**
       * GIVEN useApi hook with onSuccess callback
       * WHEN fetch succeeds
       * THEN onSuccess should be called with data
       */
      const onSuccess = vi.fn()
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ message: 'success' }),
      })

      const { result } = renderHook(() =>
        useApi<{ message: string }>('/api/test', {}, { onSuccess })
      )

      await act(async () => {
        await result.current.execute()
      })

      expect(onSuccess).toHaveBeenCalledWith({ message: 'success' })
    })

    it('should call onError callback on failed fetch', async () => {
      /**
       * GIVEN useApi hook with onError callback
       * WHEN fetch fails
       * THEN onError should be called with error message
       */
      const onError = vi.fn()
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        text: () => Promise.resolve('Server Error'),
      })

      const { result } = renderHook(() =>
        useApi<{ message: string }>('/api/test', {}, { onError })
      )

      await act(async () => {
        await result.current.execute()
      })

      expect(onError).toHaveBeenCalledWith('Server Error')
    })
  })

  describe('POST requests with body', () => {
    it('should send body as JSON for POST requests', async () => {
      /**
       * GIVEN useApi hook with POST method
       * WHEN execute is called with parameters
       * THEN fetch should be called with JSON body
       */
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      })

      const { result } = renderHook(() =>
        useApi<{ success: boolean }, { name: string }>('/api/test', { method: 'POST' })
      )

      await act(async () => {
        await result.current.execute({ name: 'test' })
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'test' }),
      })
    })
  })
})

describe('useStatus', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('should fetch from /api/status', async () => {
    /**
     * GIVEN useStatus hook
     * WHEN execute is called
     * THEN should fetch from correct endpoint
     */
    const statusData = {
      running: true,
      paused: false,
      iteration: 5,
      performer: 'task',
      performer_emoji: '📋',
      beans_pending: 3,
      beans_completed: 10,
      no_progress_count: 0,
      started_at: '2024-01-15T10:00:00',
      rate_limited_until: null,
    }

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(statusData),
    })

    const { result } = renderHook(() => useStatus())

    await act(async () => {
      await result.current.execute()
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/status', expect.any(Object))
    expect(result.current.data).toEqual(statusData)
  })
})

describe('useStart', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('should POST to /api/start with parameters', async () => {
    /**
     * GIVEN useStart hook
     * WHEN execute is called with start parameters
     * THEN should POST to correct endpoint with body
     */
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true, pid: 12345 }),
    })

    const { result } = renderHook(() => useStart())

    await act(async () => {
      await result.current.execute({ max_iterations: 10, performer: 'task' })
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_iterations: 10, performer: 'task' }),
    })
    expect(result.current.data).toEqual({ success: true, pid: 12345 })
  })
})

describe('useStop', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('should POST to /api/stop with force flag', async () => {
    /**
     * GIVEN useStop hook
     * WHEN execute is called with force flag
     * THEN should POST to correct endpoint with body
     */
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    })

    const { result } = renderHook(() => useStop())

    await act(async () => {
      await result.current.execute({ force: true })
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force: true }),
    })
  })
})
