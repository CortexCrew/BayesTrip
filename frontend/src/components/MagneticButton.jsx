import { useRef, useCallback, useState } from 'react'

/**
 * Magnetic button — subtly pulls toward cursor, glow follows mouse,
 * shine sweep on hover, ripple on click.
 */
export default function MagneticButton({
  children,
  onClick,
  variant = 'primary', // 'primary' | 'secondary' | 'gold'
  className = '',
  disabled = false,
  ...props
}) {
  const btnRef = useRef(null)
  const [ripples, setRipples] = useState([])

  const onMouseMove = useCallback((e) => {
    if (!btnRef.current || disabled) return
    const rect = btnRef.current.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    const dx = (e.clientX - cx) * 0.15
    const dy = (e.clientY - cy) * 0.15
    btnRef.current.style.transform = `translate(${dx}px, ${dy}px)`
  }, [disabled])

  const onMouseLeave = useCallback(() => {
    if (!btnRef.current) return
    btnRef.current.style.transform = 'translate(0, 0)'
  }, [])

  const onClickHandler = useCallback((e) => {
    if (disabled) return
    /* Create ripple at click position */
    const rect = btnRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const id = Date.now()
    setRipples(prev => [...prev, { id, x, y }])
    setTimeout(() => setRipples(prev => prev.filter(r => r.id !== id)), 700)
    onClick?.(e)
  }, [onClick, disabled])

  const cls = [
    'magnetic-btn',
    variant === 'gold' ? 'gold' : variant === 'secondary' ? 'secondary' : '',
    disabled ? 'disabled' : '',
    className,
  ].filter(Boolean).join(' ')

  return (
    <button
      ref={btnRef}
      className={cls}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      onClick={onClickHandler}
      disabled={disabled}
      style={{ transition: 'transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)' }}
      {...props}
    >
      <span className="btn-shine" />
      {children}
      {ripples.map(r => (
        <span
          key={r.id}
          className="btn-ripple"
          style={{ left: r.x, top: r.y, width: 20, height: 20, marginLeft: -10, marginTop: -10 }}
        />
      ))}
    </button>
  )
}
