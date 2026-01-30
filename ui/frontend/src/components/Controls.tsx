import { useState, useEffect } from 'react'
import { useStart, useStop, usePause, useResume, usePerformers } from '../hooks/useApi'
import type { StatusResponse, ProcessStatus, PerformerInfo, StartRequest } from '../types'
import { getProcessStatus } from '../types'

interface ControlsProps {
  status: StatusResponse | null
  onStatusChange?: () => void
}

export default function Controls({ status, onStatusChange }: ControlsProps) {
  const [performers, setPerformers] = useState<PerformerInfo[]>([])
  const [selectedPerformer, setSelectedPerformer] = useState<string>('')
  const [maxIterations, setMaxIterations] = useState<string>('')
  const [showOptions, setShowOptions] = useState(false)
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)

  const { execute: fetchPerformers } = usePerformers()
  const { execute: startProcess } = useStart()
  const { execute: stopProcess } = useStop()
  const { execute: pauseProcess } = usePause()
  const { execute: resumeProcess } = useResume()

  const processStatus: ProcessStatus = status ? getProcessStatus(status) : 'stopped'

  // Fetch performers on mount
  useEffect(() => {
    fetchPerformers().then((data) => {
      if (data?.performers) {
        setPerformers(data.performers)
      }
    })
  }, [fetchPerformers])

  const handleStart = async () => {
    setActionInProgress('start')
    const request: StartRequest = {}
    if (selectedPerformer) {
      request.performer = selectedPerformer
    }
    if (maxIterations) {
      const parsed = parseInt(maxIterations, 10)
      if (!isNaN(parsed) && parsed > 0) {
        request.max_iterations = parsed
      }
    }
    const result = await startProcess(request)
    if (result?.success) {
      onStatusChange?.()
      setShowOptions(false)
    }
    setActionInProgress(null)
  }

  const handleStop = async (force: boolean = false) => {
    setActionInProgress(force ? 'force_stop' : 'stop')
    const result = await stopProcess({ force })
    if (result?.success) {
      onStatusChange?.()
    }
    setActionInProgress(null)
  }

  const handlePause = async () => {
    setActionInProgress('pause')
    const result = await pauseProcess()
    if (result?.success) {
      onStatusChange?.()
    }
    setActionInProgress(null)
  }

  const handleResume = async () => {
    setActionInProgress('resume')
    const result = await resumeProcess()
    if (result?.success) {
      onStatusChange?.()
    }
    setActionInProgress(null)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Controls</h3>

      {/* Main action buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {processStatus === 'stopped' && (
          <>
            <button
              onClick={() => setShowOptions(!showOptions)}
              className="px-4 py-2 min-h-[44px] bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-white rounded-md transition-colors flex items-center gap-2"
            >
              <span>Options</span>
              <span className={`transition-transform ${showOptions ? 'rotate-180' : ''}`}>
                &#9662;
              </span>
            </button>
            <button
              onClick={handleStart}
              disabled={actionInProgress !== null}
              className="px-4 py-2 min-h-[44px] bg-green-600 hover:bg-green-500 disabled:bg-green-800 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center gap-2"
            >
              {actionInProgress === 'start' ? (
                <LoadingSpinner />
              ) : (
                <span>&#9658;</span>
              )}
              Start
            </button>
          </>
        )}

        {processStatus === 'running' && (
          <>
            <button
              onClick={handlePause}
              disabled={actionInProgress !== null}
              className="px-4 py-2 min-h-[44px] bg-yellow-600 hover:bg-yellow-500 disabled:bg-yellow-800 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center gap-2"
            >
              {actionInProgress === 'pause' ? (
                <LoadingSpinner />
              ) : (
                <span>&#10074;&#10074;</span>
              )}
              Pause
            </button>
            <button
              onClick={() => handleStop(false)}
              disabled={actionInProgress !== null}
              className="px-4 py-2 min-h-[44px] bg-red-600 hover:bg-red-500 disabled:bg-red-800 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center gap-2"
            >
              {actionInProgress === 'stop' ? (
                <LoadingSpinner />
              ) : (
                <span>&#9632;</span>
              )}
              Stop
            </button>
          </>
        )}

        {processStatus === 'paused' && (
          <>
            <button
              onClick={handleResume}
              disabled={actionInProgress !== null}
              className="px-4 py-2 min-h-[44px] bg-green-600 hover:bg-green-500 disabled:bg-green-800 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center gap-2"
            >
              {actionInProgress === 'resume' ? (
                <LoadingSpinner />
              ) : (
                <span>&#9658;</span>
              )}
              Resume
            </button>
            <button
              onClick={() => handleStop(false)}
              disabled={actionInProgress !== null}
              className="px-4 py-2 min-h-[44px] bg-red-600 hover:bg-red-500 disabled:bg-red-800 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center gap-2"
            >
              {actionInProgress === 'stop' ? (
                <LoadingSpinner />
              ) : (
                <span>&#9632;</span>
              )}
              Stop
            </button>
          </>
        )}

        {processStatus === 'rate_limited' && (
          <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
            <span>Waiting for rate limit...</span>
            <button
              onClick={() => handleStop(true)}
              disabled={actionInProgress !== null}
              className="px-4 py-2 min-h-[44px] bg-red-600 hover:bg-red-500 disabled:bg-red-800 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center gap-2"
            >
              {actionInProgress === 'force_stop' ? (
                <LoadingSpinner />
              ) : (
                <span>&#9632;</span>
              )}
              Force Stop
            </button>
          </div>
        )}
      </div>

      {/* Options panel (only shown when stopped) */}
      {processStatus === 'stopped' && showOptions && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
          {/* Performer selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Performer (optional)
            </label>
            <select
              value={selectedPerformer}
              onChange={(e) => setSelectedPerformer(e.target.value)}
              className="w-full min-h-[44px] bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Auto (based on context)</option>
              {performers.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.emoji} {p.name} - {p.description}
                </option>
              ))}
            </select>
          </div>

          {/* Max iterations input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Iterations (optional)
            </label>
            <input
              type="number"
              min="1"
              value={maxIterations}
              onChange={(e) => setMaxIterations(e.target.value)}
              placeholder="Unlimited"
              className="w-full min-h-[44px] bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Leave empty for unlimited iterations
            </p>
          </div>
        </div>
      )}

      {/* Status indicator */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <StatusIndicator status={processStatus} />
      </div>
    </div>
  )
}

function LoadingSpinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )
}

function StatusIndicator({ status }: { status: ProcessStatus }) {
  const config: Record<ProcessStatus, { color: string; bgColor: string; label: string; icon: string }> = {
    stopped: { color: 'text-gray-500 dark:text-gray-400', bgColor: 'bg-gray-500', label: 'Stopped', icon: '&#9632;' },
    running: { color: 'text-green-600 dark:text-green-400', bgColor: 'bg-green-500', label: 'Running', icon: '&#9658;' },
    paused: { color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-500', label: 'Paused', icon: '&#10074;&#10074;' },
    rate_limited: { color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-500', label: 'Rate Limited', icon: '&#9201;' },
  }

  const { color, bgColor, label, icon } = config[status]

  return (
    <div className={`flex items-center gap-2 ${color}`}>
      <span className={`w-2 h-2 rounded-full ${bgColor} animate-pulse`}></span>
      <span dangerouslySetInnerHTML={{ __html: icon }} />
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}
