import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { LOADING_STEPS } from '../utils/constants'

/**
 * Cinematic loading screen — particle assembly, sequential status messages,
 * glowing progress bar, and smooth exit transition.
 */
export default function LoadingScreen({ onComplete }) {
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(0)
  const [exiting, setExiting] = useState(false)
  const canvasRef = useRef(null)
  const particlesRef = useRef([])
  const phaseRef = useRef('scatter') // 'scatter' → 'converge' → 'done'

  /* Progress simulation (1.8s total) */
  useEffect(() => {
    const totalDuration = 1800
    const stepInterval = totalDuration / LOADING_STEPS.length
    const start = Date.now()

    const interval = setInterval(() => {
      const elapsed = Date.now() - start
      const p = Math.min(elapsed / totalDuration, 1)
      setProgress(p)
      setCurrentStep(Math.min(Math.floor(elapsed / stepInterval), LOADING_STEPS.length - 1))

      if (p >= 0.6) phaseRef.current = 'converge'

      if (p >= 1) {
        clearInterval(interval)
        phaseRef.current = 'done'
        setTimeout(() => {
          setExiting(true)
          setTimeout(() => onComplete?.(), 600)
        }, 300)
      }
    }, 30)

    return () => clearInterval(interval)
  }, [onComplete])

  /* Particle animation on canvas */
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
    }
    resize()

    /* Initialize particles scattered */
    const w = canvas.offsetWidth
    const h = canvas.offsetHeight
    const cx = w / 2
    const cy = h / 2
    const count = 80

    /* Target positions: form a simple network pattern */
    const targets = []
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2
      const ring = i % 3
      const r = 60 + ring * 40
      targets.push({ x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r })
    }

    particlesRef.current = Array.from({ length: count }, (_, i) => ({
      x: Math.random() * w,
      y: Math.random() * h,
      tx: targets[i].x,
      ty: targets[i].y,
      r: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.5 + 0.3,
    }))

    const draw = () => {
      ctx.clearRect(0, 0, w, h)
      const pts = particlesRef.current
      const phase = phaseRef.current

      for (const p of pts) {
        if (phase === 'converge' || phase === 'done') {
          p.x += (p.tx - p.x) * 0.04
          p.y += (p.ty - p.y) * 0.04
        } else {
          p.x += (Math.random() - 0.5) * 0.8
          p.y += (Math.random() - 0.5) * 0.8
        }

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(0, 240, 255, ${p.alpha})`
        ctx.fill()
      }

      /* Draw connections between nearby converged particles */
      if (phase === 'converge' || phase === 'done') {
        for (let i = 0; i < pts.length; i++) {
          for (let j = i + 1; j < pts.length; j++) {
            const dx = pts[i].x - pts[j].x
            const dy = pts[i].y - pts[j].y
            const dist = Math.sqrt(dx * dx + dy * dy)
            if (dist < 80) {
              ctx.beginPath()
              ctx.moveTo(pts[i].x, pts[i].y)
              ctx.lineTo(pts[j].x, pts[j].y)
              ctx.strokeStyle = `rgba(0, 240, 255, ${(1 - dist / 80) * 0.15})`
              ctx.lineWidth = 0.5
              ctx.stroke()
            }
          }
        }
      }

      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)

    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <AnimatePresence>
      {!exiting && (
        <motion.div
          className="loading-screen"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.05, filter: 'blur(10px)' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Particle canvas */}
          <canvas
            ref={canvasRef}
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              opacity: 0.6,
            }}
          />

          {/* Content */}
          <motion.div
            className="loading-title"
            initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            BAYESTRIP
          </motion.div>

          <motion.div
            className="loading-subtitle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            INITIALIZING INTELLIGENCE ENGINE
          </motion.div>

          {/* Steps */}
          <div className="loading-steps">
            {LOADING_STEPS.map((step, i) => (
              <div
                key={i}
                className={`loading-step ${i === currentStep ? 'active' : i < currentStep ? 'done' : ''}`}
              >
                {i < currentStep ? '✓ ' : i === currentStep ? '▸ ' : '  '}{step}
              </div>
            ))}
          </div>

          {/* Progress bar */}
          <div className="loading-progress-track">
            <div className="loading-progress-bar" style={{ width: `${progress * 100}%` }} />
            <div className="loading-scanline" />
          </div>

          <div className="loading-percent">
            {Math.round(progress * 100)}%
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
