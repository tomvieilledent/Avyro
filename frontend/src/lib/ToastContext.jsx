import { createContext, useCallback, useContext, useRef, useState } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null) // { msg, type }
  const timerRef = useRef(null)

  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type })
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setToast(null), 3500)
  }, [])

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div id="toast" className={toast ? `toast-${toast.type}` : ''}>
        <span id="toast-msg">{toast?.msg}</span>
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
