import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

let toastId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = `toast-${++toastId}`
    setToasts((prev) => [...prev, { id, message, type }])

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 5000)
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-20 md:bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  )
}

interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const config: Record<ToastType, { bg: string; icon: string; border: string }> = {
    success: {
      bg: 'bg-green-100 dark:bg-green-900/80',
      icon: '✓',
      border: 'border-green-300 dark:border-green-700',
    },
    error: {
      bg: 'bg-red-100 dark:bg-red-900/80',
      icon: '✕',
      border: 'border-red-300 dark:border-red-700',
    },
    warning: {
      bg: 'bg-yellow-100 dark:bg-yellow-900/80',
      icon: '!',
      border: 'border-yellow-300 dark:border-yellow-700',
    },
    info: {
      bg: 'bg-blue-100 dark:bg-blue-900/80',
      icon: 'i',
      border: 'border-blue-300 dark:border-blue-700',
    },
  }

  const { bg, icon, border } = config[toast.type]

  return (
    <div
      className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${bg} ${border} animate-slide-in-right`}
      role="alert"
    >
      <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-white dark:bg-gray-800 text-sm font-bold">
        {icon}
      </span>
      <p className="flex-1 text-sm text-gray-800 dark:text-gray-100">{toast.message}</p>
      <button
        onClick={() => onRemove(toast.id)}
        className="flex-shrink-0 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
        aria-label="Dismiss"
      >
        <span className="text-gray-500 dark:text-gray-400">✕</span>
      </button>
    </div>
  )
}
