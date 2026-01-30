import { useTheme } from '../context/ThemeContext'

function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const options = [
    { value: 'light' as const, icon: '☀️', label: 'Light' },
    { value: 'dark' as const, icon: '🌙', label: 'Dark' },
    { value: 'system' as const, icon: '💻', label: 'System' },
  ]

  return (
    <div className="flex items-center gap-1 p-1 rounded-lg bg-gray-200 dark:bg-gray-700">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => setTheme(option.value)}
          className={`p-2 rounded-md text-sm transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center ${
            theme === option.value
              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
          title={option.label}
          aria-label={`Switch to ${option.label} theme`}
        >
          <span className="text-lg">{option.icon}</span>
        </button>
      ))}
    </div>
  )
}

export default ThemeToggle
