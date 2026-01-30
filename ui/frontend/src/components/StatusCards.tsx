import type { StatusResponse, ProcessStatus } from '../types'
import { getProcessStatus } from '../types'

interface StatusCardsProps {
  status: StatusResponse | null
  loading: boolean
  connected: boolean
}

interface CardProps {
  title: string
  value: string | number
  icon: string
  subtitle?: string
  highlight?: boolean
}

function Card({ title, value, icon, subtitle, highlight }: CardProps) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg p-4 border ${
        highlight ? 'border-primary-500' : 'border-gray-200 dark:border-gray-700'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">{title}</span>
      </div>
      <div className="mt-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">{value}</span>
        {subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: ProcessStatus }) {
  const config: Record<ProcessStatus, { color: string; label: string }> = {
    stopped: { color: 'bg-gray-500', label: 'Stopped' },
    running: { color: 'bg-green-500', label: 'Running' },
    paused: { color: 'bg-yellow-500', label: 'Paused' },
    rate_limited: { color: 'bg-red-500', label: 'Rate Limited' },
  }

  const { color, label } = config[status]

  return (
    <div className="flex items-center gap-2">
      <span className={`w-3 h-3 rounded-full ${color} animate-pulse`}></span>
      <span className="text-lg font-medium text-gray-900 dark:text-gray-100">{label}</span>
    </div>
  )
}

function ConnectionBadge({ connected }: { connected: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`}
      ></span>
      <span className="text-gray-500 dark:text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
    </div>
  )
}

export default function StatusCards({ status, loading, connected }: StatusCardsProps) {
  if (loading && !status) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const processStatus = status ? getProcessStatus(status) : 'stopped'
  const performer = status?.performer_emoji
    ? `${status.performer_emoji} ${status.performer}`
    : status?.performer ?? 'None'

  return (
    <div className="space-y-4">
      {/* Status header */}
      <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <StatusBadge status={processStatus} />
        <ConnectionBadge connected={connected} />
      </div>

      {/* Status cards grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card
          title="Iteration"
          value={status?.iteration ?? '-'}
          icon="🔄"
          subtitle={status?.no_progress_count ? `${status.no_progress_count} no progress` : undefined}
          highlight={processStatus === 'running'}
        />
        <Card
          title="Performer"
          value={performer}
          icon="🎭"
        />
        <Card
          title="Tasks Pending"
          value={status?.beans_pending ?? 0}
          icon="📋"
        />
        <Card
          title="Tasks Done"
          value={status?.beans_completed ?? 0}
          icon="✅"
        />
      </div>

      {/* Rate limited countdown */}
      {status?.rate_limited_until && (
        <RateLimitedCountdown until={status.rate_limited_until} />
      )}
    </div>
  )
}

function RateLimitedCountdown({ until }: { until: string }) {
  const endTime = new Date(until)
  const now = new Date()
  const diffMs = endTime.getTime() - now.getTime()
  const diffMins = Math.max(0, Math.ceil(diffMs / 60000))

  return (
    <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-4">
      <div className="flex items-center gap-2">
        <span className="text-xl">⏳</span>
        <span className="text-red-700 dark:text-red-300">
          Rate limited. Resuming in ~{diffMins} minute{diffMins !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  )
}
