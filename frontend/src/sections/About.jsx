import { motion } from 'framer-motion'
import SectionTransition from '../components/SectionTransition'
import ParticleField from '../components/ParticleField'

const TECH_STACK = [
  { icon: '🔮', name: 'Bayesian Network' },
  { icon: '⚡', name: 'HMM + Viterbi' },
  { icon: '⚛️', name: 'React' },
  { icon: '🎨', name: 'Three.js' },
  { icon: '🐍', name: 'FastAPI' },
  { icon: '📊', name: 'Pandas / NumPy' },
  { icon: '🎬', name: 'GSAP' },
  { icon: '🗺️', name: 'Leaflet' },
]

const FACTS = [
  { label: 'Destinations', value: '20', unit: 'places' },
  { label: 'Evidence Variables', value: '5', unit: 'inputs' },
  { label: 'Time Slots', value: '3', unit: 'periods' },
  { label: 'Transition Matrix', value: '20×20', unit: 'states' },
]

export default function About() {
  return (
    <SectionTransition id="about" variant="default">
      <ParticleField count={20} color="rgba(168,85,247,0.2)" connectionColor="rgba(168,85,247,0.04)" />

      <div className="section-header">
        <div className="section-label" style={{ color: '#a855f7' }}>ABOUT THE PROJECT</div>
        <h2 className="section-title">BayesTrip</h2>
        <p className="section-subtitle">
          A probabilistic tourist recommendation system for Chennai.
          Built as a Semester 5 Pattern Recognition project.
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: '16px',
        marginBottom: '48px',
      }}>
        {FACTS.map((fact, i) => (
          <motion.div
            key={fact.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1, duration: 0.5 }}
            style={{
              textAlign: 'center',
              padding: '20px 12px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '12px',
            }}
          >
            <div style={{
              fontFamily: "'Orbitron', sans-serif",
              fontSize: '1.5rem',
              fontWeight: 800,
              color: '#a855f7',
              textShadow: '0 0 20px rgba(168,85,247,0.3)',
            }}>
              {fact.value}
            </div>
            <div style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: '0.7rem',
              color: '#8888aa',
              marginTop: '4px',
            }}>
              {fact.label}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Algorithm summary */}
      <div style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: '16px',
        padding: '32px',
        marginBottom: '48px',
      }}>
        <h3 style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '0.85rem',
          fontWeight: 600,
          letterSpacing: '0.08em',
          color: '#e8e8e8',
          marginBottom: '16px',
        }}>
          THE MATHEMATICS
        </h3>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.78rem',
          color: '#00f0ff',
          lineHeight: 2,
          overflowX: 'auto',
        }}>
          <div>Score(Pᵢ) ∝ P(Pᵢ) × Π P(Eₖ | Pᵢ)</div>
          <div style={{ color: '#8888aa', fontSize: '0.68rem' }}>
            Posterior = Prior × Likelihood, normalized over all places
          </div>
          <div style={{ marginTop: '12px' }}>
            δₜ(j) = B_j(Oₜ) × max_i [δₜ₋₁(i) × A_ij]
          </div>
          <div style={{ color: '#8888aa', fontSize: '0.68rem' }}>
            Viterbi recurrence — decoded via backtracking
          </div>
        </div>
      </div>

      {/* Tech stack */}
      <h3 style={{
        fontFamily: "'Orbitron', sans-serif",
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.1em',
        color: '#8888aa',
        textAlign: 'center',
        marginBottom: '20px',
      }}>
        BUILT WITH
      </h3>
      <div className="tech-stack-grid">
        {TECH_STACK.map((tech, i) => (
          <motion.div
            key={tech.name}
            className="tech-card"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.05, duration: 0.4 }}
          >
            <div className="tech-icon">{tech.icon}</div>
            <div className="tech-name">{tech.name}</div>
          </motion.div>
        ))}
      </div>

      {/* Footer */}
      <div style={{
        textAlign: 'center',
        marginTop: '64px',
        paddingTop: '32px',
        borderTop: '1px solid rgba(255,255,255,0.04)',
      }}>
        <div style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '0.7rem',
          fontWeight: 600,
          letterSpacing: '0.1em',
          color: '#55556a',
        }}>
          BAYESTRIP · SEMESTER 5 · PATTERN RECOGNITION
        </div>
        <div style={{
          fontFamily: "'Inter', sans-serif",
          fontSize: '0.7rem',
          color: '#55556a',
          marginTop: '8px',
        }}>
          Bayesian inference + HMM/Viterbi • 20 Chennai destinations • React + Three.js + FastAPI
        </div>
      </div>
    </SectionTransition>
  )
}
