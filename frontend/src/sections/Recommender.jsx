import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import SectionTransition from '../components/SectionTransition'
import MagneticButton from '../components/MagneticButton'
import ParticleField from '../components/ParticleField'
import { EVIDENCE_OPTIONS, EVIDENCE_LABELS, OPTION_ICONS, COMPUTATION_STEPS } from '../utils/constants'
import { fetchOptions, fetchRecommendation } from '../utils/api'

/**
 * Recommender section — interactive evidence selection cards + computation overlay.
 */
export default function Recommender({ onResults }) {
  const [options, setOptions] = useState(EVIDENCE_OPTIONS)
  const [selected, setSelected] = useState({})
  const [computing, setComputing] = useState(false)
  const [compStep, setCompStep] = useState(0)
  const [error, setError] = useState(null)

  /* Fetch real options from backend on mount */
  useEffect(() => {
    fetchOptions().then(setOptions).catch(() => { /* use defaults */ })
  }, [])

  const allSelected = Object.keys(options).every(k => selected[k])

  const select = useCallback((group, value) => {
    setSelected(prev => ({ ...prev, [group]: value }))
    setError(null)
  }, [])

  const submit = useCallback(async () => {
    if (!allSelected) return
    setComputing(true)
    setCompStep(0)
    setError(null)

    /* Animate through computation steps */
    const stepTimer = setInterval(() => {
      setCompStep(prev => {
        if (prev >= COMPUTATION_STEPS.length - 1) {
          clearInterval(stepTimer)
          return prev
        }
        return prev + 1
      })
    }, 350)

    try {
      const result = await fetchRecommendation(selected)
      /* Wait for computation animation to finish */
      clearInterval(stepTimer)
      setCompStep(COMPUTATION_STEPS.length - 1)
      await new Promise(r => setTimeout(r, 600))
      setComputing(false)
      onResults?.(result)

      /* Scroll to results */
      setTimeout(() => {
        const el = document.getElementById('results')
        if (el) el.scrollIntoView({ behavior: 'smooth' })
      }, 200)
    } catch (err) {
      clearInterval(stepTimer)
      setComputing(false)
      setError(err.message || 'An error occurred.')
    }
  }, [allSelected, selected, onResults])

  return (
    <>
      <SectionTransition id="recommend" variant="default">
        <ParticleField count={25} color="rgba(0,240,255,0.2)" />

        <div className="section-header">
          <div className="section-label">RECOMMENDATION ENGINE</div>
          <h2 className="section-title">Configure Your Journey</h2>
          <p className="section-subtitle">
            Select your preferences below. The Bayesian Network will compute
            the optimal destinations for you.
          </p>
        </div>

        {/* Evidence groups */}
        {Object.entries(options).map(([group, choices]) => (
          <div key={group} className="evidence-group">
            <div className="group-label">{EVIDENCE_LABELS[group] || group}</div>
            <div className="evidence-options">
              {choices.map(choice => (
                <div
                  key={choice}
                  className={`selection-card ${selected[group] === choice ? 'selected' : ''}`}
                  onClick={() => select(group, choice)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && select(group, choice)}
                >
                  <div className="card-icon">{OPTION_ICONS[choice] || '●'}</div>
                  <div className="card-label">{choice}</div>
                  <div className="check-mark">
                    {selected[group] === choice ? '✓' : ''}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Error message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="state-message"
            style={{ padding: '20px' }}
          >
            <div className="state-icon">⚠️</div>
            <div className="state-title">CONNECTION INTERRUPTED</div>
            <div className="state-desc">{error}</div>
            <MagneticButton onClick={submit}>Retry Connection</MagneticButton>
          </motion.div>
        )}

        {/* Submit */}
        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <MagneticButton
            variant="gold"
            onClick={submit}
            disabled={!allSelected || computing}
          >
            {computing ? 'Computing...' : 'Generate My Trip'}
          </MagneticButton>
          {!allSelected && (
            <p style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.7rem',
              color: '#55556a',
              marginTop: '12px',
            }}>
              Select one option from each category above
            </p>
          )}
        </div>
      </SectionTransition>

      {/* ── Computation Overlay ────────────────────────────────── */}
      <AnimatePresence>
        {computing && (
          <motion.div
            className="computation-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            {/* Pulsing network circle */}
            <motion.div
              style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                border: '2px solid rgba(0,240,255,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '20px',
              }}
              animate={{
                boxShadow: [
                  '0 0 20px rgba(0,240,255,0.1)',
                  '0 0 40px rgba(0,240,255,0.3)',
                  '0 0 20px rgba(0,240,255,0.1)',
                ],
              }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              <motion.div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  border: '2px solid rgba(0,240,255,0.4)',
                }}
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
              />
            </motion.div>

            {/* Step messages */}
            {COMPUTATION_STEPS.map((step, i) => (
              <motion.div
                key={i}
                className={`computation-step ${i === compStep ? 'active' : i < compStep ? 'done' : ''}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{
                  opacity: i <= compStep ? 1 : 0,
                  x: i <= compStep ? 0 : -10,
                }}
                transition={{ duration: 0.3 }}
              >
                {i < compStep ? '✓ ' : i === compStep ? '▸ ' : ''}{step}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
