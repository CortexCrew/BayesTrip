import { useEffect, useRef } from 'react'
import { motion, useInView } from 'framer-motion'

/**
 * Cinematic section transition wrapper — light sweep + opacity shift.
 * Wraps around a section to animate its entrance.
 */
export default function SectionTransition({
  children,
  id,
  className = '',
  variant = 'default', // 'default' | 'warm' (for travel sections)
}) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-15% 0px' })

  const sweepColor = variant === 'warm'
    ? 'rgba(255, 167, 38, 0.06)'
    : 'rgba(0, 240, 255, 0.04)'

  return (
    <section id={id} className={`section ${className}`} ref={ref}>
      {/* Light sweep on entry */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(180deg, transparent 0%, ${sweepColor} 50%, transparent 100%)`,
          opacity: isInView ? 1 : 0,
          transition: 'opacity 1.5s ease',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      <motion.div
        className="section-content"
        initial={{ opacity: 0, y: 40 }}
        animate={isInView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      >
        {children}
      </motion.div>
    </section>
  )
}
