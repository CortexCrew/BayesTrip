import { useRef, useEffect, useCallback } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

/**
 * 2D canvas particle background — floating dots with faint connections.
 * Much lighter than Three.js, used for sections without a full 3D scene.
 */
export default function ParticleField({
  count = 60,
  color = 'rgba(0, 240, 255, 0.4)',
  connectionColor = 'rgba(0, 240, 255, 0.06)',
  connectionDistance = 120,
  speed = 0.3,
  className = '',
  style = {},
}) {
  const canvasRef = useRef(null)
  const reduced = useReducedMotion()
  const particles = useRef([])
  const mouse = useRef({ x: -9999, y: -9999 })

  const init = useCallback((w, h) => {
    particles.current = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * speed,
      vy: (Math.random() - 0.5) * speed,
      r: Math.random() * 1.5 + 0.5,
    }))
  }, [count, speed])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let raf

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio, 2)
      canvas.width = canvas.offsetWidth * dpr
      canvas.height = canvas.offsetHeight * dpr
      ctx.scale(dpr, dpr)
      init(canvas.offsetWidth, canvas.offsetHeight)
    }
    resize()
    window.addEventListener('resize', resize)

    const onMouse = (e) => {
      const rect = canvas.getBoundingClientRect()
      mouse.current.x = e.clientX - rect.left
      mouse.current.y = e.clientY - rect.top
    }
    canvas.addEventListener('mousemove', onMouse, { passive: true })

    const draw = () => {
      const w = canvas.offsetWidth
      const h = canvas.offsetHeight
      ctx.clearRect(0, 0, w, h)

      const pts = particles.current
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i]
        if (!reduced) {
          p.x += p.vx
          p.y += p.vy
          if (p.x < 0 || p.x > w) p.vx *= -1
          if (p.y < 0 || p.y > h) p.vy *= -1
        }

        /* Draw particle */
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()

        /* Connections */
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j]
          const dx = p.x - q.x
          const dy = p.y - q.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < connectionDistance) {
            ctx.beginPath()
            ctx.moveTo(p.x, p.y)
            ctx.lineTo(q.x, q.y)
            ctx.strokeStyle = connectionColor
            ctx.lineWidth = 0.5
            ctx.globalAlpha = 1 - dist / connectionDistance
            ctx.stroke()
            ctx.globalAlpha = 1
          }
        }
      }
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      canvas.removeEventListener('mousemove', onMouse)
    }
  }, [color, connectionColor, connectionDistance, reduced, init])

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
        ...style,
      }}
    />
  )
}
