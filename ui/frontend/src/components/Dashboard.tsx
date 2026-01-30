import { useEffect, useState, useCallback } from 'react'
import { useStatus } from '../hooks/useApi'
import { useWebSocket } from '../hooks/useWebSocket'
import StatusCards from './StatusCards'
import Controls from './Controls'
import LiveOutput from './LiveOutput'
import type { StatusResponse, WSMessage } from '../types'

export default function Dashboard() {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const { execute: fetchStatus, loading } = useStatus()

  // Fetch initial status
  useEffect(() => {
    fetchStatus().then((data) => {
      if (data) setStatus(data)
    })
  }, [fetchStatus])

  // Handle WebSocket messages
  const handleMessage = useCallback((message: WSMessage) => {
    if (message.event === 'status_change') {
      // Refetch status on status change
      fetchStatus().then((data) => {
        if (data) setStatus(data)
      })
    } else if (message.event === 'iteration_start') {
      // Update iteration number optimistically
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              iteration: message.data.iteration as number,
              performer: message.data.performer as string,
              performer_emoji: message.data.performer_emoji as string | null,
            }
          : prev
      )
    } else if (message.event === 'iteration_end') {
      // Refetch to get updated bean counts
      fetchStatus().then((data) => {
        if (data) setStatus(data)
      })
    }
  }, [fetchStatus])

  const { connected } = useWebSocket('/ws', {
    onMessage: handleMessage,
    onOpen: () => {
      // Refetch status when reconnecting
      fetchStatus().then((data) => {
        if (data) setStatus(data)
      })
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <button
          onClick={() => fetchStatus().then((data) => data && setStatus(data))}
          className="px-3 py-1 text-sm bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <StatusCards status={status} loading={loading} connected={connected} />

      {/* Controls */}
      <Controls
        status={status}
        onStatusChange={() => fetchStatus().then((data) => data && setStatus(data))}
      />

      {/* Started at info */}
      {status?.started_at && (
        <div className="text-sm text-gray-400">
          Started at: {new Date(status.started_at).toLocaleString()}
        </div>
      )}

      {/* Live Output */}
      <div className="h-96">
        <LiveOutput maxLines={1000} />
      </div>
    </div>
  )
}
