import { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { useWhiteboard, useUpdateWhiteboard } from '../hooks/useApi'

function Whiteboard() {
  const { data, loading, error, execute: fetchWhiteboard } = useWhiteboard()
  const { loading: saving, error: saveError, execute: saveWhiteboard } = useUpdateWhiteboard()

  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')

  // Fetch whiteboard on mount
  useEffect(() => {
    fetchWhiteboard()
  }, [])

  // Auto-refresh every 30 seconds when not editing
  useEffect(() => {
    if (isEditing) return

    const interval = setInterval(() => {
      fetchWhiteboard()
    }, 30000)

    return () => clearInterval(interval)
  }, [isEditing, fetchWhiteboard])

  // Format last modified date
  const formatLastModified = useCallback((dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    return date.toLocaleString()
  }, [])

  // Start editing
  const handleEdit = () => {
    setEditContent(data?.content || '')
    setIsEditing(true)
  }

  // Cancel editing
  const handleCancel = () => {
    setEditContent('')
    setIsEditing(false)
  }

  // Save changes
  const handleSave = async () => {
    const result = await saveWhiteboard({ content: editContent })
    if (result?.success) {
      setIsEditing(false)
      setEditContent('')
      fetchWhiteboard()
    }
  }

  // Refresh
  const handleRefresh = () => {
    fetchWhiteboard()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Whiteboard</h1>
        <div className="flex items-center gap-2">
          {!isEditing && (
            <>
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 min-h-[44px] bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 transition-colors"
              >
                {loading ? '...' : 'Refresh'}
              </button>
              <button
                onClick={handleEdit}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 min-h-[44px] bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
              >
                Edit
              </button>
            </>
          )}
          {isEditing && (
            <>
              <button
                onClick={handleCancel}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 min-h-[44px] bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 min-h-[44px] bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Last modified */}
      {data?.last_modified && !isEditing && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Last modified: {formatLastModified(data.last_modified)}
        </div>
      )}

      {/* Error messages */}
      {error && (
        <div className="p-4 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 rounded-lg text-red-700 dark:text-red-300">
          Error loading whiteboard: {error}
        </div>
      )}
      {saveError && (
        <div className="p-4 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 rounded-lg text-red-700 dark:text-red-300">
          Error saving whiteboard: {saveError}
        </div>
      )}

      {/* Loading state */}
      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-500 dark:text-gray-400">Loading whiteboard...</div>
        </div>
      )}

      {/* Edit mode */}
      {isEditing && (
        <div className="space-y-4">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full h-[600px] bg-gray-50 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg p-4 text-gray-900 dark:text-gray-100 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            placeholder="Write your notes here..."
            disabled={saving}
          />
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Tip: Use Markdown for formatting (headings, lists, bold, etc.)
          </div>
        </div>
      )}

      {/* View mode - Markdown rendered */}
      {!isEditing && data && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 min-h-[400px]">
          {data.content ? (
            <div className="prose dark:prose-invert prose-gray max-w-none">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4 pb-2 border-b border-gray-200 dark:border-gray-700">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mt-6 mb-3">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mt-4 mb-2">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-gray-700 dark:text-gray-300 mb-3 leading-relaxed">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-3 space-y-1">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside text-gray-700 dark:text-gray-300 mb-3 space-y-1">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-gray-700 dark:text-gray-300">{children}</li>
                  ),
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300 underline"
                    >
                      {children}
                    </a>
                  ),
                  code: ({ children }) => (
                    <code className="bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200 px-1.5 py-0.5 rounded text-sm font-mono">
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-4 overflow-x-auto mb-4">
                      {children}
                    </pre>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-600 dark:text-gray-400 my-4">
                      {children}
                    </blockquote>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-bold text-gray-900 dark:text-gray-100">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic text-gray-700 dark:text-gray-300">{children}</em>
                  ),
                  hr: () => <hr className="border-gray-200 dark:border-gray-700 my-6" />,
                }}
              >
                {data.content}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-12">
              The whiteboard is empty. Click "Edit" to add content.
            </p>
          )}
        </div>
      )}

      {/* Help text */}
      <div className="text-sm text-gray-500 text-center">
        The whiteboard is used for communication between Claude instances. It auto-refreshes every
        30 seconds.
      </div>
    </div>
  )
}

export default Whiteboard
