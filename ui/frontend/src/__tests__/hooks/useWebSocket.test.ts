import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '../../hooks/useWebSocket'

// Create a simpler mock WebSocket that immediately opens
let mockWebSocketInstance: MockWebSocket | null = null

class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState: number = MockWebSocket.CONNECTING // Start as CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  sentMessages: string[] = []

  constructor(url: string) {
    this.url = url
    mockWebSocketInstance = this
    // Immediately call onopen on next tick and set OPEN
    queueMicrotask(() => {
      this.readyState = MockWebSocket.OPEN
      this.onopen?.(new Event('open'))
    })
  }

  send(data: string) {
    this.sentMessages.push(data)
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close'))
  }

  // Helper to simulate receiving a message
  simulateMessage(data: object) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }))
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', MockWebSocket)
    mockWebSocketInstance = null
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.unstubAllGlobals()
    mockWebSocketInstance = null
  })

  describe('connection management', () => {
    it('should initialize as disconnected then become connected', async () => {
      /**
       * GIVEN useWebSocket hook is rendered
       * WHEN WebSocket opens
       * THEN connected should become true
       */
      const { result } = renderHook(() => useWebSocket('/ws'))

      // Initially disconnected
      expect(result.current.connected).toBe(false)

      // Wait for connection to open
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      expect(result.current.connected).toBe(true)
    })

    it('should call onOpen callback when connected', async () => {
      /**
       * GIVEN useWebSocket hook with onOpen callback
       * WHEN WebSocket connection opens
       * THEN onOpen should be called
       */
      const onOpen = vi.fn()
      renderHook(() => useWebSocket('/ws', { onOpen }))

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      expect(onOpen).toHaveBeenCalled()
    })

    it('should call onClose callback when disconnected', async () => {
      /**
       * GIVEN a connected WebSocket
       * WHEN connection closes
       * THEN onClose should be called
       */
      const onClose = vi.fn()
      renderHook(() => useWebSocket('/ws', { onClose }))

      // Wait for connection
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      // Close the connection
      await act(async () => {
        mockWebSocketInstance?.close()
      })

      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('URL resolution', () => {
    it('should convert relative URL to absolute WebSocket URL', async () => {
      /**
       * GIVEN a relative WebSocket URL
       * WHEN hook is rendered
       * THEN should create WebSocket with resolved URL
       */
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          host: 'localhost:3000',
        },
        writable: true,
      })

      renderHook(() => useWebSocket('/ws'))

      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      expect(mockWebSocketInstance?.url).toBe('ws://localhost:3000/ws')
    })
  })

  describe('send functionality', () => {
    it('should send message when connected', async () => {
      /**
       * GIVEN a connected WebSocket
       * WHEN send is called
       * THEN should send JSON stringified message
       */
      const { result } = renderHook(() => useWebSocket('/ws'))

      // Wait for connection
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      act(() => {
        result.current.send({ action: 'ping' })
      })

      expect(mockWebSocketInstance?.sentMessages).toContain(JSON.stringify({ action: 'ping' }))
    })

    it('should warn when sending while disconnected', () => {
      /**
       * GIVEN a disconnected WebSocket
       * WHEN send is called
       * THEN should log a warning
       */
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { result } = renderHook(() => useWebSocket('/ws'))

      // Don't wait for connection - send immediately
      act(() => {
        result.current.send({ action: 'ping' })
      })

      expect(consoleSpy).toHaveBeenCalledWith(
        'WebSocket not connected, cannot send message'
      )

      consoleSpy.mockRestore()
    })
  })

  describe('reconnect functionality', () => {
    it('should provide reconnect function', () => {
      /**
       * GIVEN useWebSocket hook
       * WHEN rendered
       * THEN reconnect function should be available
       */
      const { result } = renderHook(() => useWebSocket('/ws'))

      expect(typeof result.current.reconnect).toBe('function')
    })

    it('should create new connection on manual reconnect', async () => {
      /**
       * GIVEN a WebSocket hook
       * WHEN reconnect is called manually
       * THEN should create a new connection
       */
      const { result } = renderHook(() => useWebSocket('/ws'))

      // Wait for initial connection
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      const firstInstance = mockWebSocketInstance

      // Reconnect manually
      act(() => {
        result.current.reconnect()
      })

      // Wait for new connection
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      // Should have created a new WebSocket instance
      expect(mockWebSocketInstance).not.toBe(firstInstance)
    })
  })

  describe('message handling', () => {
    it('should parse and pass messages to onMessage callback', async () => {
      /**
       * GIVEN a connected WebSocket with onMessage callback
       * WHEN a message is received
       * THEN onMessage should be called with parsed message
       */
      const onMessage = vi.fn()
      renderHook(() => useWebSocket('/ws', { onMessage }))

      // Wait for connection
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      // Simulate a message
      await act(async () => {
        mockWebSocketInstance?.simulateMessage({ event: 'test', data: { foo: 'bar' } })
      })

      expect(onMessage).toHaveBeenCalledWith({ event: 'test', data: { foo: 'bar' } })
    })
  })
})
