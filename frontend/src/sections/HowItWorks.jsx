import { useState, useEffect, useRef, Suspense } from 'react'
import { motion, useInView } from 'framer-motion'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import SectionTransition from '../components/SectionTransition'
import BayesianNetwork3D from '../three/BayesianNetwork3D'
import ParticleField from '../components/ParticleField'

gsap.registerPlugin(ScrollTrigger)

const PIPELINE_STEPS = [
  {
    number: '01',
    icon: '🧬',
    title: 'USER EVIDENCE',
    desc: 'You provide five preferences: Age, Budget, Interest, Travel Type, and Weather. These become observed evidence variables.',
    color: 'cyan',
    nodes: ['age', 'budget', 'interest', 'travel_type', 'weather'],
  },
  {
    number: '02',
    icon: '🔮',
    title: 'BAYESIAN NETWORK',
    desc: 'A probabilistic graphical model computes P(Place | Evidence) — the posterior probability of each destination given your preferences.',
    color: 'cyan',
    nodes: ['age', 'budget', 'interest', 'travel_type', 'weather'],
  },
  {
    number: '03',
    icon: '🏆',
    title: 'TOP-5 SELECTION',
    desc: 'The five destinations with the highest posterior probabilities are selected as your recommended places.',
    color: 'purple',
    nodes: [],
  },
  {
    number: '04',
    icon: '⚡',
    title: 'HMM + VITERBI',
    desc: 'A Hidden Markov Model sequences the Top-5 into an optimal visiting order across Morning, Afternoon, and Evening slots using Viterbi decoding.',
    color: 'gold',
    nodes: [],
  },
]

/* ── HMM Timeline Visualization ──────────────────────────────── */
function HMMTimeline({ visible }) {
  const slots = ['MORNING', 'AFTERNOON', 'EVENING']

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      margin: '24px 0',
      opacity: visible ? 1 : 0.3,
      transition: 'opacity 0.6s ease',
    }}>
      {slots.map((slot, i) => (
        <div key={slot} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={visible ? { scale: 1, opacity: 1 } : {}}
            transition={{ delay: i * 0.2, duration: 0.5 }}
            style={{
              padding: '12px 20px',
              background: 'rgba(255,167,38,0.06)',
              border: '1px solid rgba(255,167,38,0.2)',
              borderRadius: '8px',
              fontFamily: "'Orbitron', sans-serif",
              fontSize: '0.65rem',
              fontWeight: 600,
              letterSpacing: '0.1em',
              color: '#ffa726',
              textAlign: 'center',
            }}
          >
            {slot}
            <div style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.55rem',
              color: '#8888aa',
              marginTop: '4px',
            }}>
              {i === 0 ? '09:00-12:00' : i === 1 ? '13:00-17:00' : '17:30-20:30'}
            </div>
          </motion.div>
          {i < slots.length - 1 && (
            <motion.div
              initial={{ scaleX: 0 }}
              animate={visible ? { scaleX: 1 } : {}}
              transition={{ delay: i * 0.2 + 0.3, duration: 0.4 }}
              style={{
                width: '40px',
                height: '2px',
                background: 'linear-gradient(90deg, rgba(255,167,38,0.5), rgba(168,85,247,0.3))',
                transformOrigin: 'left',
              }}
            />
          )}
        </div>
      ))}
    </div>
  )
}

export default function HowItWorks({ tier }) {
  const [activeStep, setActiveStep] = useState(0)
  const sectionRef = useRef(null)
  const stepsRef = useRef(null)

  /* ScrollTrigger: advance steps as user scrolls */
  useEffect(() => {
    if (!stepsRef.current) return

    const triggers = []
    const stepEls = stepsRef.current.querySelectorAll('.pipeline-step')
    stepEls.forEach((el, i) => {
      const st = ScrollTrigger.create({
        trigger: el,
        start: 'top 70%',
        onEnter: () => setActiveStep(i),
        onLeaveBack: () => setActiveStep(Math.max(0, i - 1)),
      })
      triggers.push(st)
    })

    return () => triggers.forEach(st => st.kill())
  }, [])

  const currentNodes = PIPELINE_STEPS[activeStep]?.nodes || []
  const showHMM = activeStep >= 3

  return (
    <SectionTransition id="how" className="" variant="default">
      <ParticleField count={30} color="rgba(0,240,255,0.25)" connectionDistance={100} />

      <div className="section-header">
        <div className="section-label">THE ALGORITHM</div>
        <h2 className="section-title">How BayesTrip Works</h2>
        <p className="section-subtitle">
          From your preferences to a personalized itinerary — a four-stage
          probabilistic intelligence pipeline.
        </p>
      </div>

      {/* 3D Bayesian Network (activates with scroll) */}
      {tier !== 'low' && (
        <Suspense fallback={null}>
          <BayesianNetwork3D activeNodes={currentNodes} />
        </Suspense>
      )}

      {/* Pipeline steps */}
      <div ref={stepsRef} className="pipeline-steps" style={{ marginTop: '20px' }}>
        {PIPELINE_STEPS.map((step, i) => (
          <motion.div
            key={i}
            className="pipeline-step"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={{ delay: i * 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            style={{
              borderColor: activeStep === i
                ? step.color === 'cyan' ? 'rgba(0,240,255,0.25)' : step.color === 'gold' ? 'rgba(255,167,38,0.25)' : 'rgba(168,85,247,0.25)'
                : undefined,
              boxShadow: activeStep === i
                ? `0 0 30px ${step.color === 'cyan' ? 'rgba(0,240,255,0.08)' : step.color === 'gold' ? 'rgba(255,167,38,0.08)' : 'rgba(168,85,247,0.08)'}`
                : undefined,
            }}
          >
            <div className="step-number">{step.number}</div>
            <div className="step-icon">{step.icon}</div>
            <div className="step-title">{step.title}</div>
            <div className="step-desc">{step.desc}</div>
          </motion.div>
        ))}
      </div>

      {/* HMM Timeline */}
      <div style={{ marginTop: '40px' }}>
        <HMMTimeline visible={showHMM} />
        {showHMM && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              textAlign: 'center',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.75rem',
              color: '#8888aa',
              marginTop: '12px',
            }}
          >
            Viterbi path = argmax P(state sequence | observations)
          </motion.p>
        )}
      </div>
    </SectionTransition>
  )
}
