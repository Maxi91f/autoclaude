import { useState, useEffect, useMemo } from 'react'
import { useTasks } from '../hooks/useApi'
import type { TaskInfo } from '../types'

// Priority badge colors
const priorityColors: Record<string, string> = {
  critical: 'bg-red-500 text-white',
  high: 'bg-orange-500 text-white',
  normal: 'bg-yellow-500 text-gray-900',
  low: 'bg-green-500 text-white',
  deferred: 'bg-gray-500 text-white',
}

// Type badge colors
const typeColors: Record<string, string> = {
  feature: 'bg-purple-600 text-white',
  bug: 'bg-red-600 text-white',
  task: 'bg-blue-600 text-white',
  epic: 'bg-indigo-600 text-white',
  chore: 'bg-gray-600 text-white',
}

// Status display order and colors
const statusConfig: Record<string, { label: string; bgColor: string; textColor: string; order: number }> = {
  'in-progress': { label: 'In Progress', bgColor: 'bg-blue-900/50', textColor: 'text-blue-300', order: 0 },
  'todo': { label: 'To Do', bgColor: 'bg-yellow-900/50', textColor: 'text-yellow-300', order: 1 },
  'completed': { label: 'Completed', bgColor: 'bg-green-900/50', textColor: 'text-green-300', order: 2 },
  'cancelled': { label: 'Cancelled', bgColor: 'bg-gray-900/50', textColor: 'text-gray-400', order: 3 },
}

// Priority sort order (critical first)
const priorityOrder: Record<string, number> = {
  critical: 0,
  high: 1,
  normal: 2,
  low: 3,
  deferred: 4,
}

type SortBy = 'priority' | 'status' | 'title'
type SortOrder = 'asc' | 'desc'

interface CollapsedSections {
  [key: string]: boolean
}

function PriorityBadge({ priority }: { priority: string }) {
  const colorClass = priorityColors[priority] || priorityColors.normal
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {priority}
    </span>
  )
}

function TypeBadge({ type }: { type: string }) {
  const colorClass = typeColors[type] || typeColors.task
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {type}
    </span>
  )
}

function TaskCard({ task }: { task: TaskInfo }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-100 truncate">{task.title}</h3>
          <p className="text-sm text-gray-400 mt-1">{task.id}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <TypeBadge type={task.type} />
          <PriorityBadge priority={task.priority} />
        </div>
      </div>

      {task.body && (
        <div className="mt-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-gray-400 hover:text-gray-300 flex items-center gap-1"
          >
            <span className={`transform transition-transform ${expanded ? 'rotate-90' : ''}`}>
              {'>'}
            </span>
            {expanded ? 'Hide details' : 'Show details'}
          </button>
          {expanded && (
            <div className="mt-2 text-sm text-gray-300 bg-gray-900 rounded p-3 whitespace-pre-wrap overflow-x-auto">
              {task.body}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface TaskSectionProps {
  status: string
  tasks: TaskInfo[]
  collapsed: boolean
  onToggle: () => void
}

function TaskSection({ status, tasks, collapsed, onToggle }: TaskSectionProps) {
  const config = statusConfig[status] || statusConfig.todo

  return (
    <div className="mb-6">
      <button
        onClick={onToggle}
        className={`w-full flex items-center justify-between p-3 rounded-lg ${config.bgColor} hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-center gap-2">
          <span className={`transform transition-transform ${collapsed ? '' : 'rotate-90'}`}>
            {'>'}
          </span>
          <h2 className={`text-lg font-semibold ${config.textColor}`}>{config.label}</h2>
          <span className={`px-2 py-0.5 rounded-full text-xs ${config.textColor} bg-black/20`}>
            {tasks.length}
          </span>
        </div>
      </button>

      {!collapsed && (
        <div className="mt-3 space-y-3">
          {tasks.length === 0 ? (
            <p className="text-gray-500 text-sm italic px-3">No tasks</p>
          ) : (
            tasks.map((task) => <TaskCard key={task.id} task={task} />)
          )}
        </div>
      )}
    </div>
  )
}

function TaskList() {
  const { data, loading, error, execute: fetchTasks } = useTasks()

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')

  // Sorting
  const [sortBy, setSortBy] = useState<SortBy>('priority')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')

  // Collapsed sections
  const [collapsedSections, setCollapsedSections] = useState<CollapsedSections>({
    completed: true,
    cancelled: true,
  })

  // Fetch on mount
  useEffect(() => {
    fetchTasks()
  }, [])

  // Get unique types from tasks
  const availableTypes = useMemo(() => {
    if (!data?.tasks) return []
    const types = new Set(data.tasks.map((t) => t.type))
    return Array.from(types).sort()
  }, [data?.tasks])

  // Filter and sort tasks
  const filteredTasks = useMemo(() => {
    if (!data?.tasks) return []

    let tasks = [...data.tasks]

    // Apply status filter
    if (statusFilter !== 'all') {
      tasks = tasks.filter((t) => t.status === statusFilter)
    }

    // Apply type filter
    if (typeFilter !== 'all') {
      tasks = tasks.filter((t) => t.type === typeFilter)
    }

    // Sort
    tasks.sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'priority':
          comparison = (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2)
          break
        case 'status':
          comparison = (statusConfig[a.status]?.order || 1) - (statusConfig[b.status]?.order || 1)
          break
        case 'title':
          comparison = a.title.localeCompare(b.title)
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return tasks
  }, [data?.tasks, statusFilter, typeFilter, sortBy, sortOrder])

  // Group tasks by status
  const tasksByStatus = useMemo(() => {
    const groups: Record<string, TaskInfo[]> = {
      'in-progress': [],
      'todo': [],
      'completed': [],
      'cancelled': [],
    }

    for (const task of filteredTasks) {
      const status = task.status in groups ? task.status : 'todo'
      groups[status].push(task)
    }

    // Sort within each group by priority
    for (const status in groups) {
      groups[status].sort((a, b) =>
        (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2)
      )
    }

    return groups
  }, [filteredTasks])

  const toggleSection = (status: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [status]: !prev[status],
    }))
  }

  const handleRefresh = () => {
    fetchTasks()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-100">Tasks</h1>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
        >
          <span className={loading ? 'animate-spin' : ''}>
            {loading ? '...' : 'Refresh'}
          </span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All</option>
            <option value="in-progress">In Progress</option>
            <option value="todo">To Do</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Type:</label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">All</option>
            {availableTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="priority">Priority</option>
            <option value="status">Status</option>
            <option value="title">Title</option>
          </select>
          <button
            onClick={() => setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
            className="px-2 py-1.5 bg-gray-700 border border-gray-600 rounded text-sm hover:bg-gray-600 transition-colors"
            title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
          >
            {sortOrder === 'asc' ? 'Asc' : 'Desc'}
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
          Error loading tasks: {error}
        </div>
      )}

      {/* Loading state */}
      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-400">Loading tasks...</div>
        </div>
      )}

      {/* Task sections */}
      {data && statusFilter === 'all' && (
        <div>
          {Object.entries(statusConfig)
            .sort(([, a], [, b]) => a.order - b.order)
            .map(([status]) => (
              <TaskSection
                key={status}
                status={status}
                tasks={tasksByStatus[status] || []}
                collapsed={collapsedSections[status] || false}
                onToggle={() => toggleSection(status)}
              />
            ))}
        </div>
      )}

      {/* Filtered view (no grouping) */}
      {data && statusFilter !== 'all' && (
        <div className="space-y-3">
          {filteredTasks.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No tasks match the current filters</p>
          ) : (
            filteredTasks.map((task) => <TaskCard key={task.id} task={task} />)
          )}
        </div>
      )}

      {/* Summary */}
      {data && (
        <div className="text-sm text-gray-500 text-center pt-4 border-t border-gray-700">
          Showing {filteredTasks.length} of {data.tasks.length} tasks
        </div>
      )}
    </div>
  )
}

export default TaskList
