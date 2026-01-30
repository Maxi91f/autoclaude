import { useEffect, useRef, useState, useCallback } from 'react'
import type { WSMessage, WSClientMessage } from '../types'

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface UseWebSocketReturn {
  connected: boolean
  send: (message: WSClientMessage) => void
  reconnect: () => void
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options

  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimeoutRef = useRef<number | null>(null)

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    // Resolve WebSocket URL
    const wsUrl = url.startsWith('/')
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${url}`
      : url

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setConnected(true)
      reconnectAttempts.current = 0
      onOpen?.()
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      onClose?.()

      // Attempt to reconnect
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, reconnectInterval)
      }
    }

    ws.onerror = (event) => {
      onError?.(event)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSMessage
        onMessage?.(message)
      } catch {
        console.error('Failed to parse WebSocket message:', event.data)
      }
    }

    wsRef.current = ws
  }, [url, onMessage, onOpen, onClose, onError, reconnectInterval, maxReconnectAttempts])

  const send = useCallback((message: WSClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }, [])

  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0
    connect()
  }, [connect])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected, send, reconnect }
}
