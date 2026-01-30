import { useState, useEffect, useMemo, useCallback } from 'react'
import { useHistoryStats, useHistoryPerformers } from '../hooks/useApi'
import type { IterationInfo, HistoryResponse, IterationResult } from '../types'

// Result badge colors and labels
const resultConfig: Record<IterationResult, { label: string; bgColor: string; textColor: string; icon: string }> = {
  success: {
    label: 'Success',
    bgColor: 'bg-green-100 dark:bg-green-900/50',
    textColor: 'text-green-700 dark:text-green-300',
    icon: '✓',
  },
  no_progress: {
    label: 'No Progress',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/50',
    textColor: 'text-yellow-700 dark:text-yellow-300',
    icon: '⚠',
  },
  error: {
    label: 'Error',
    bgColor: 'bg-red-100 dark:bg-red-900/50',
    textColor: 'text-red-700 dark:text-red-300',
    icon: '✗',
  },
  rate_limited: {
    label: 'Rate Limited',
    bgColor: 'bg-orange-100 dark:bg-orange-900/50',
    textColor: 'text-orange-700 dark:text-orange-300',
    icon: '⏳',
  },
  cancelled: {
    label: 'Cancelled',
    bgColor: 'bg-gray-100 dark:bg-gray-900/50',
    textColor: 'text-gray-600 dark:text-gray-400',
    icon: '⊘',
  },
}

function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return 'Today'
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday'
  }
  return date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })
}

function getDateKey(dateString: string): string {
  return new Date(dateString).toDateString()
}

function ResultBadge({ result }: { result: IterationResult }) {
  const config = resultConfig[result] || resultConfig.success
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.bgColor} ${config.textColor}`}>
      <span>{config.icon}</span>
      {config.label}
    </span>
  )
}

function IterationCard({ iteration }: { iteration: IterationInfo }) {
  const [expanded, setExpanded] = useState(false)
  const config = resultConfig[iteration.result] || resultConfig.success
  const tasksDiff = iteration.tasks_after - iteration.tasks_before

  return (
    <div className={`relative pl-8 pb-6 last:pb-0`}>
      {/* Timeline connector */}
      <div className="absolute left-3 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-700" />

      {/* Timeline dot */}
      <div
        className={`absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center text-xs ${config.bgColor} ${config.textColor} border-2 border-white dark:border-gray-800`}
      >
        {config.icon}
      </div>

      {/* Card content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-lg">{iteration.performer_emoji || '🤖'}</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {iteration.performer_name}
              </span>
              <span className="text-gray-500 dark:text-gray-400 text-sm">
                #{iteration.iteration_number}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500 dark:text-gray-400">
              <span>{formatTime(iteration.started_at)}</span>
              <span>•</span>
              <span>{formatDuration(iteration.duration_seconds)}</span>
              {tasksDiff !== 0 && (
                <>
                  <span>•</span>
                  <span className={tasksDiff < 0 ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {tasksDiff < 0 ? `${Math.abs(tasksDiff)} task${Math.abs(tasksDiff) !== 1 ? 's' : ''} completed` : `${tasksDiff} new task${tasksDiff !== 1 ? 's' : ''}`}
                  </span>
                </>
              )}
            </div>
          </div>
          <ResultBadge result={iteration.result} />
        </div>

        {/* Error message (if any) */}
        {iteration.error_message && (
          <div className="mt-3">
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 flex items-center gap-1 min-h-[44px] py-2"
            >
              <span className={`transform transition-transform ${expanded ? 'rotate-90' : ''}`}>
                {'>'}
              </span>
              {expanded ? 'Hide error' : 'Show error'}
            </button>
            {expanded && (
              <div className="mt-2 text-sm text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/30 rounded p-3 font-mono overflow-x-auto">
                {iteration.error_message}
              </div>
            )}
          </div>
        )}

        {/* Task counts */}
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span>Tasks before: {iteration.tasks_before}</span>
          <span>Tasks after: {iteration.tasks_after}</span>
        </div>
      </div>
    </div>
  )
}

interface DayGroupProps {
  date: string
  iterations: IterationInfo[]
  collapsed: boolean
  onToggle: () => void
}

function DayGroup({ date, iterations, collapsed, onToggle }: DayGroupProps) {
  const successCount = iterations.filter((i) => i.result === 'success').length
  const errorCount = iterations.filter((i) => i.result === 'error' || i.result === 'no_progress').length

  return (
    <div className="mb-6">
      <button
        onClick={onToggle}
        className="w-full min-h-[44px] flex items-center justify-between p-3 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`transform transition-transform ${collapsed ? '' : 'rotate-90'}`}>
            {'>'}
          </span>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{date}</h2>
          <span className="px-2 py-0.5 rounded-full text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            {iterations.length} iteration{iterations.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {successCount > 0 && (
            <span className="text-green-600 dark:text-green-400">
              {successCount} ✓
            </span>
          )}
          {errorCount > 0 && (
            <span className="text-red-600 dark:text-red-400">
              {errorCount} ✗
            </span>
          )}
        </div>
      </button>

      {!collapsed && (
        <div className="mt-4 ml-2">
          {iterations.map((iteration) => (
            <IterationCard key={iteration.id} iteration={iteration} />
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, subtext }: { label: string; value: string | number; subtext?: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
      <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</div>
      {subtext && <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">{subtext}</div>}
    </div>
  )
}

function History() {
  const [iterations, setIterations] = useState<IterationInfo[]>([])
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [resultFilter, setResultFilter] = useState<string>('all')
  const [performerFilter, setPerformerFilter] = useState<string>('all')

  // Collapsed day groups
  const [collapsedDays, setCollapsedDays] = useState<Record<string, boolean>>({})

  // Stats and performers
  const { data: stats, execute: fetchStats } = useHistoryStats()
  const { data: performers, execute: fetchPerformers } = useHistoryPerformers()

  const PAGE_SIZE = 50

  // Fetch history data
  const fetchHistory = useCallback(async (reset: boolean = true) => {
    if (reset) {
      setLoading(true)
      setIterations([])
    } else {
      setLoadingMore(true)
    }
    setError(null)

    const offset = reset ? 0 : iterations.length

    try {
      const params = new URLSearchParams({
        limit: PAGE_SIZE.toString(),
        offset: offset.toString(),
      })

      if (resultFilter !== 'all') {
        params.set('result', resultFilter)
      }
      if (performerFilter !== 'all') {
        params.set('performer', performerFilter)
      }

      const response = await fetch(`/api/history?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`)
      }

      const data: HistoryResponse = await response.json()

      if (reset) {
        setIterations(data.iterations)
      } else {
        setIterations((prev) => [...prev, ...data.iterations])
      }
      setTotal(data.total)
      setHasMore(data.has_more)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [iterations.length, resultFilter, performerFilter])

  // Fetch on mount and when filters change
  useEffect(() => {
    fetchHistory(true)
    fetchStats()
    fetchPerformers()
  }, [resultFilter, performerFilter])

  // Group iterations by day
  const iterationsByDay = useMemo(() => {
    const groups: Record<string, IterationInfo[]> = {}

    for (const iteration of iterations) {
      const dateKey = getDateKey(iteration.ended_at)
      if (!groups[dateKey]) {
        groups[dateKey] = []
      }
      groups[dateKey].push(iteration)
    }

    // Sort days by date (newest first)
    const sortedDays = Object.entries(groups).sort(([a], [b]) => {
      return new Date(b).getTime() - new Date(a).getTime()
    })

    return sortedDays
  }, [iterations])

  const toggleDay = (dateKey: string) => {
    setCollapsedDays((prev) => ({
      ...prev,
      [dateKey]: !prev[dateKey],
    }))
  }

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      fetchHistory(false)
    }
  }

  const handleRefresh = () => {
    fetchHistory(true)
    fetchStats()
    fetchPerformers()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">History</h1>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 min-h-[44px] bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 transition-colors"
        >
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Total Iterations"
            value={stats.total}
          />
          <StatCard
            label="Success Rate"
            value={stats.total > 0 ? `${Math.round((stats.success_count / stats.total) * 100)}%` : '0%'}
            subtext={`${stats.success_count} successful`}
          />
          <StatCard
            label="Errors"
            value={stats.error_count + stats.no_progress_count}
            subtext={`${stats.error_count} errors, ${stats.no_progress_count} no progress`}
          />
          <StatCard
            label="Avg Duration"
            value={formatDuration(stats.avg_duration_seconds)}
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 dark:text-gray-400">Result:</label>
          <select
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
            className="min-h-[44px] bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All</option>
            <option value="success">Success</option>
            <option value="no_progress">No Progress</option>
            <option value="error">Error</option>
            <option value="rate_limited">Rate Limited</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 dark:text-gray-400">Performer:</label>
          <select
            value={performerFilter}
            onChange={(e) => setPerformerFilter(e.target.value)}
            className="min-h-[44px] bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All Performers</option>
            {performers?.performers.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 rounded-lg text-red-700 dark:text-red-300">
          Error loading history: {error}
        </div>
      )}

      {/* Loading state */}
      {loading && iterations.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-500 dark:text-gray-400">Loading history...</div>
        </div>
      )}

      {/* Empty state */}
      {!loading && iterations.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="text-4xl mb-4">📜</div>
          <div className="text-gray-500 dark:text-gray-400 text-lg">No iteration history yet</div>
          <div className="text-gray-400 dark:text-gray-500 text-sm mt-2">
            Run AutoClaude to start building history
          </div>
        </div>
      )}

      {/* Timeline by day */}
      {iterationsByDay.length > 0 && (
        <div>
          {iterationsByDay.map(([dateKey, dayIterations]) => (
            <DayGroup
              key={dateKey}
              date={formatDate(dayIterations[0].ended_at)}
              iterations={dayIterations}
              collapsed={collapsedDays[dateKey] || false}
              onToggle={() => toggleDay(dateKey)}
            />
          ))}
        </div>
      )}

      {/* Load more button */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="px-6 py-3 min-h-[44px] bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 transition-colors"
          >
            {loadingMore ? 'Loading...' : `Load More (${iterations.length} of ${total})`}
          </button>
        </div>
      )}

      {/* Summary */}
      {iterations.length > 0 && (
        <div className="text-sm text-gray-500 dark:text-gray-400 text-center pt-4 border-t border-gray-200 dark:border-gray-700">
          Showing {iterations.length} of {total} iterations
        </div>
      )}
    </div>
  )
}

export default History
