import { useState, useCallback, useMemo } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAutoScroll } from '../hooks/useAutoScroll'
import type { OutputLine, WSMessage, OutputLineType } from '../types'

interface OutputLineConfig {
  icon: string
  bgColor: string
  textColor: string
  borderColor: string
}

const LINE_TYPE_CONFIG: Record<OutputLineType, OutputLineConfig> = {
  thinking: {
    icon: '',
    bgColor: 'bg-gray-100 dark:bg-gray-800/50',
    textColor: 'text-gray-500 dark:text-gray-400 italic',
    borderColor: 'border-l-gray-400 dark:border-l-gray-500',
  },
  tool_use: {
    icon: '',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    textColor: 'text-blue-700 dark:text-blue-300',
    borderColor: 'border-l-blue-500',
  },
  tool_result: {
    icon: '',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    textColor: 'text-green-700 dark:text-green-300',
    borderColor: 'border-l-green-500',
  },
  error: {
    icon: '',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    textColor: 'text-red-700 dark:text-red-300',
    borderColor: 'border-l-red-500',
  },
  text: {
    icon: '',
    bgColor: 'bg-transparent',
    textColor: 'text-gray-800 dark:text-gray-200',
    borderColor: 'border-l-transparent',
  },
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function getTypeLabel(type: OutputLineType): string {
  switch (type) {
    case 'thinking':
      return 'thinking'
    case 'tool_use':
      return 'tool'
    case 'tool_result':
      return 'result'
    case 'error':
      return 'error'
    default:
      return ''
  }
}

interface OutputLineRowProps {
  line: OutputLine
  showTimestamp: boolean
}

function OutputLineRow({ line, showTimestamp }: OutputLineRowProps) {
  const config = LINE_TYPE_CONFIG[line.type]
  const label = getTypeLabel(line.type)

  return (
    <div
      className={`flex items-start gap-2 px-3 py-1.5 border-l-4 ${config.bgColor} ${config.borderColor} font-mono text-sm`}
    >
      {showTimestamp && (
        <span className="text-gray-400 dark:text-gray-500 text-xs shrink-0 w-16">
          {formatTimestamp(line.timestamp)}
        </span>
      )}
      {config.icon && <span className="shrink-0">{config.icon}</span>}
      {label && (
        <span className="text-xs uppercase tracking-wide text-gray-400 dark:text-gray-500 shrink-0 w-14">
          [{label}]
        </span>
      )}
      <span className={`${config.textColor} whitespace-pre-wrap break-all flex-1`}>
        {line.content}
      </span>
    </div>
  )
}

interface LiveOutputProps {
  maxLines?: number
}

export default function LiveOutput({ maxLines = 1000 }: LiveOutputProps) {
  const [lines, setLines] = useState<OutputLine[]>([])
  const [showTimestamps, setShowTimestamps] = useState(true)
  const [copySuccess, setCopySuccess] = useState(false)

  const {
    containerRef,
    autoScrollEnabled,
    toggleAutoScroll,
    scrollToBottom,
  } = useAutoScroll({ enabled: true })

  // Handle WebSocket messages
  const handleMessage = useCallback(
    (message: WSMessage) => {
      if (message.event === 'output_line') {
        const newLine: OutputLine = {
          type: message.data.type as OutputLineType,
          content: message.data.content as string,
          timestamp: message.data.timestamp as string,
        }

        setLines((prev) => {
          const updated = [...prev, newLine]
          // Keep only the last maxLines
          if (updated.length > maxLines) {
            return updated.slice(-maxLines)
          }
          return updated
        })
      } else if (message.event === 'iteration_start') {
        // Add a separator for new iteration
        setLines((prev) => [
          ...prev,
          {
            type: 'text',
            content: `--- Iteration ${message.data.iteration} started (${message.data.performer || 'unknown performer'}) ---`,
            timestamp: new Date().toISOString(),
          },
        ])
      } else if (message.event === 'iteration_end') {
        // Add a separator for iteration end
        setLines((prev) => [
          ...prev,
          {
            type: 'text',
            content: `--- Iteration ${message.data.iteration} ended (${message.data.result || 'unknown result'}) ---`,
            timestamp: new Date().toISOString(),
          },
        ])
      }
    },
    [maxLines]
  )

  const { connected } = useWebSocket('/ws', {
    onMessage: handleMessage,
  })

  // Copy all output to clipboard
  const copyToClipboard = useCallback(async () => {
    const text = lines
      .map((line) => {
        const time = formatTimestamp(line.timestamp)
        const label = getTypeLabel(line.type)
        return label ? `[${time}] [${label}] ${line.content}` : `[${time}] ${line.content}`
      })
      .join('\n')

    try {
      await navigator.clipboard.writeText(text)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }, [lines])

  // Clear output
  const clearOutput = useCallback(() => {
    setLines([])
  }, [])

  // Filter stats
  const stats = useMemo(() => {
    const counts: Record<OutputLineType, number> = {
      thinking: 0,
      tool_use: 0,
      tool_result: 0,
      error: 0,
      text: 0,
    }
    lines.forEach((line) => {
      counts[line.type]++
    })
    return counts
  }, [lines])

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-gray-900 dark:text-white">Live Output</h3>
          <div className="flex items-center gap-1">
            <span
              className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}
            />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Stats */}
          <div className="hidden sm:flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mr-2">
            <span>{lines.length} lines</span>
            {stats.error > 0 && (
              <span className="text-red-600 dark:text-red-400">{stats.error} errors</span>
            )}
          </div>

          {/* Toggle timestamps */}
          <button
            onClick={() => setShowTimestamps(!showTimestamps)}
            className={`px-2 py-1 min-h-[32px] text-xs rounded transition-colors ${
              showTimestamps
                ? 'bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
            title="Toggle timestamps"
          >
            Time
          </button>

          {/* Toggle auto-scroll */}
          <button
            onClick={toggleAutoScroll}
            className={`px-2 py-1 min-h-[32px] text-xs rounded transition-colors ${
              autoScrollEnabled
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
            title={autoScrollEnabled ? 'Disable auto-scroll' : 'Enable auto-scroll'}
          >
            Auto
          </button>

          {/* Scroll to bottom */}
          <button
            onClick={scrollToBottom}
            className="px-2 py-1 min-h-[32px] text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 rounded transition-colors"
            title="Scroll to bottom"
          >
            Bottom
          </button>

          {/* Copy button */}
          <button
            onClick={copyToClipboard}
            className={`px-2 py-1 min-h-[32px] text-xs rounded transition-colors ${
              copySuccess
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
            title="Copy all output to clipboard"
          >
            {copySuccess ? 'Copied!' : 'Copy'}
          </button>

          {/* Clear button */}
          <button
            onClick={clearOutput}
            className="px-2 py-1 min-h-[32px] text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 rounded transition-colors"
            title="Clear output"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Output container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto min-h-0"
      >
        {lines.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-500">
            <div className="text-center">
              <p className="text-lg">No output yet</p>
              <p className="text-sm mt-1">
                {connected
                  ? 'Waiting for output from Claude...'
                  : 'Connecting to server...'}
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-800/50">
            {lines.map((line, index) => (
              <OutputLineRow
                key={`${line.timestamp}-${index}`}
                line={line}
                showTimestamp={showTimestamps}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer with auto-scroll indicator */}
      {!autoScrollEnabled && lines.length > 0 && (
        <div className="px-4 py-2 bg-gray-100 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-center">
          <button
            onClick={toggleAutoScroll}
            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300"
          >
            Auto-scroll paused. Click to resume.
          </button>
        </div>
      )}
    </div>
  )
}
