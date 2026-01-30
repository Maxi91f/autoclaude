import { useState, useCallback } from 'react'

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void
  onError?: (error: string) => void
}

interface UseApiReturn<T, P = void> {
  data: T | null
  loading: boolean
  error: string | null
  execute: P extends void ? () => Promise<T | null> : (params: P) => Promise<T | null>
}

export function useApi<T, P = void>(
  url: string,
  options: RequestInit = {},
  hookOptions: UseApiOptions<T> = {}
): UseApiReturn<T, P> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(
    async (params?: P): Promise<T | null> => {
      setLoading(true)
      setError(null)

      try {
        const fetchOptions: RequestInit = {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        }

        if (params !== undefined && options.method !== 'GET') {
          fetchOptions.body = JSON.stringify(params)
        }

        const response = await fetch(url, fetchOptions)

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(errorText || `HTTP error ${response.status}`)
        }

        const result = (await response.json()) as T
        setData(result)
        hookOptions.onSuccess?.(result)
        return result
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error'
        setError(errorMessage)
        hookOptions.onError?.(errorMessage)
        return null
      } finally {
        setLoading(false)
      }
    },
    [url, options, hookOptions]
  )

  return { data, loading, error, execute: execute as UseApiReturn<T, P>['execute'] }
}

// Convenience hooks for common API calls
export function useStatus() {
  return useApi<import('../types').StatusResponse>('/api/status')
}

export function useStart() {
  return useApi<import('../types').StartResponse, import('../types').StartRequest>(
    '/api/start',
    { method: 'POST' }
  )
}

export function useStop() {
  return useApi<import('../types').SimpleResponse, import('../types').StopRequest>(
    '/api/stop',
    { method: 'POST' }
  )
}

export function usePause() {
  return useApi<import('../types').SimpleResponse>('/api/pause', { method: 'POST' })
}

export function useResume() {
  return useApi<import('../types').SimpleResponse>('/api/resume', { method: 'POST' })
}

export function usePerformers() {
  return useApi<import('../types').PerformersResponse>('/api/performers')
}
