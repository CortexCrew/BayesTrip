import { useState, useEffect } from 'react'

/** Returns true when the user prefers reduced motion. */
export function useReducedMotion() {
  const [reduced, setReduced] = useState(false)

  useEffect(() => {
    const mq = matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(mq.matches)
    const handler = (e) => setReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return reduced
}
