import { useRef, useCallback } from 'react'

/**
 * Glass-morphism card with 3D tilt on hover and cursor-following glow.
 */
export default function GlassCard({ children, className = '', style = {}, tiltMax = 8, ...props }) {
  const cardRef = useRef(null)
  const glowRef = useRef(null)

  const onMouseMove = useCallback((e) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    const rotateX = (0.5 - y) * tiltMax
    const rotateY = (x - 0.5) * tiltMax
    cardRef.current.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`

    /* Move glow to cursor pos */
    if (glowRef.current) {
      glowRef.current.style.left = `${e.clientX - rect.left}px`
      glowRef.current.style.top = `${e.clientY - rect.top}px`
    }
  }, [tiltMax])

  const onMouseLeave = useCallback(() => {
    if (cardRef.current) {
      cardRef.current.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)'
    }
  }, [])

  return (
    <div
      ref={cardRef}
      className={`glass-card ${className}`}
      style={{ transition: 'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)', ...style }}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      {...props}
    >
      <div ref={glowRef} className="card-glow" />
      {children}
    </div>
  )
}
