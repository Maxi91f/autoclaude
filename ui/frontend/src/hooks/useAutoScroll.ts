import { useRef, useCallback, useEffect } from 'react'

interface UseAutoScrollOptions {
  /** Threshold in pixels from bottom to consider "at bottom" */
  threshold?: number
  /** Whether auto-scroll is enabled by default */
  enabled?: boolean
}

interface UseAutoScrollReturn {
  /** Ref to attach to the scrollable container */
  containerRef: React.RefObject<HTMLDivElement>
  /** Whether the user is currently at the bottom */
  isAtBottom: boolean
  /** Whether auto-scroll is enabled */
  autoScrollEnabled: boolean
  /** Toggle auto-scroll on/off */
  toggleAutoScroll: () => void
  /** Enable auto-scroll */
  enableAutoScroll: () => void
  /** Disable auto-scroll */
  disableAutoScroll: () => void
  /** Scroll to bottom immediately */
  scrollToBottom: () => void
}

export function useAutoScroll(options: UseAutoScrollOptions = {}): UseAutoScrollReturn {
  const { threshold = 50, enabled = true } = options

  const containerRef = useRef<HTMLDivElement>(null)
  const isAtBottomRef = useRef(true)
  const autoScrollEnabledRef = useRef(enabled)
  // Force re-render when these change
  const forceUpdateRef = useRef(0)

  const checkIsAtBottom = useCallback(() => {
    const container = containerRef.current
    if (!container) return true

    const { scrollTop, scrollHeight, clientHeight } = container
    return scrollHeight - scrollTop - clientHeight <= threshold
  }, [threshold])

  const scrollToBottom = useCallback(() => {
    const container = containerRef.current
    if (!container) return

    container.scrollTo({
      top: container.scrollHeight,
      behavior: 'smooth',
    })
    isAtBottomRef.current = true
  }, [])

  const toggleAutoScroll = useCallback(() => {
    autoScrollEnabledRef.current = !autoScrollEnabledRef.current
    if (autoScrollEnabledRef.current) {
      scrollToBottom()
    }
    forceUpdateRef.current++
  }, [scrollToBottom])

  const enableAutoScroll = useCallback(() => {
    autoScrollEnabledRef.current = true
    scrollToBottom()
    forceUpdateRef.current++
  }, [scrollToBottom])

  const disableAutoScroll = useCallback(() => {
    autoScrollEnabledRef.current = false
    forceUpdateRef.current++
  }, [])

  // Handle scroll events to detect user scrolling up
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleScroll = () => {
      const atBottom = checkIsAtBottom()
      isAtBottomRef.current = atBottom

      // If user scrolls up, disable auto-scroll
      if (!atBottom && autoScrollEnabledRef.current) {
        // User manually scrolled up, disable auto-scroll
        autoScrollEnabledRef.current = false
        forceUpdateRef.current++
      }
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => container.removeEventListener('scroll', handleScroll)
  }, [checkIsAtBottom])

  // MutationObserver to auto-scroll when new content is added
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const observer = new MutationObserver(() => {
      if (autoScrollEnabledRef.current && isAtBottomRef.current) {
        // Use requestAnimationFrame to ensure DOM is updated
        requestAnimationFrame(() => {
          container.scrollTop = container.scrollHeight
        })
      }
    })

    observer.observe(container, {
      childList: true,
      subtree: true,
    })

    return () => observer.disconnect()
  }, [])

  return {
    containerRef,
    isAtBottom: isAtBottomRef.current,
    autoScrollEnabled: autoScrollEnabledRef.current,
    toggleAutoScroll,
    enableAutoScroll,
    disableAutoScroll,
    scrollToBottom,
  }
}
