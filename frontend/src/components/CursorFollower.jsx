import { useEffect, useRef, useCallback } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

/**
 * Custom cursor system — glowing dot + trailing ring.
 * Expands on hovering interactive elements, hidden on touch devices.
 */
export default function CursorFollower() {
  const dotRef = useRef(null)
  const ringRef = useRef(null)
  const pos = useRef({ x: -100, y: -100 })
  const ringPos = useRef({ x: -100, y: -100 })
  const hovering = useRef(false)
  const reduced = useReducedMotion()

  const onMove = useCallback((e) => {
    pos.current.x = e.clientX
    pos.current.y = e.clientY
  }, [])

  useEffect(() => {
    if (reduced) return
    const isTouch = matchMedia('(hover: none) and (pointer: coarse)').matches
    if (isTouch) return

    window.addEventListener('mousemove', onMove, { passive: true })

    /* Detect interactive elements under cursor */
    const onOver = (e) => {
      const tag = e.target.tagName
      const interactive = e.target.closest('button, a, [role="button"], .selection-card, .glass-card, .magnetic-btn, .destination-card, .tech-card, canvas')
      if (interactive || tag === 'CANVAS') {
        hovering.current = true
        dotRef.current?.classList.add('hovering')
        ringRef.current?.classList.add('hovering')
      }
    }
    const onOut = () => {
      hovering.current = false
      dotRef.current?.classList.remove('hovering')
      ringRef.current?.classList.remove('hovering')
    }

    document.addEventListener('mouseover', onOver, { passive: true })
    document.addEventListener('mouseout', onOut, { passive: true })

    /* Animation loop — dot follows exactly, ring lerps with delay */
    let raf
    const animate = () => {
      if (dotRef.current) {
        dotRef.current.style.transform = `translate(${pos.current.x - 3}px, ${pos.current.y - 3}px)`
      }
      ringPos.current.x += (pos.current.x - ringPos.current.x) * 0.12
      ringPos.current.y += (pos.current.y - ringPos.current.y) * 0.12
      if (ringRef.current) {
        ringRef.current.style.transform = `translate(${ringPos.current.x - 18}px, ${ringPos.current.y - 18}px)`
      }
      raf = requestAnimationFrame(animate)
    }
    raf = requestAnimationFrame(animate)

    return () => {
      window.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseover', onOver)
      document.removeEventListener('mouseout', onOut)
      cancelAnimationFrame(raf)
    }
  }, [onMove, reduced])

  if (reduced) return null
  const isTouch = typeof matchMedia !== 'undefined' && matchMedia('(hover: none) and (pointer: coarse)').matches
  if (isTouch) return null

  return (
    <>
      <div ref={dotRef} className="cursor-dot" />
      <div ref={ringRef} className="cursor-ring" />
    </>
  )
}
