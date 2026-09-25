import { useState, useEffect } from 'react'

/** Returns scroll progress 0→1 for the whole page. */
export function useScrollProgress() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const update = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight
      setProgress(h > 0 ? window.scrollY / h : 0)
    }
    window.addEventListener('scroll', update, { passive: true })
    update()
    return () => window.removeEventListener('scroll', update)
  }, [])

  return progress
}
