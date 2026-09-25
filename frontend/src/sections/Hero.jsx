import { useRef, useEffect, Suspense } from 'react'
import { motion } from 'framer-motion'
import gsap from 'gsap'
import HeroScene from '../three/HeroScene'
import MagneticButton from '../components/MagneticButton'

/**
 * Hero section — full-screen 3D Bayesian network scene with
 * cinematic title reveal, subtitle, and CTAs.
 */
export default function Hero({ tier }) {
  const mouse = useRef({ x: 0, y: 0 })
  const titleRef = useRef(null)
  const subtitleRef = useRef(null)
  const descRef = useRef(null)
  const ctaRef = useRef(null)

  /* Track mouse for 3D parallax */
  useEffect(() => {
    const onMove = (e) => {
      mouse.current.x = (e.clientX / window.innerWidth - 0.5) * 2
      mouse.current.y = -(e.clientY / window.innerHeight - 0.5) * 2
    }
    window.addEventListener('mousemove', onMove, { passive: true })
    return () => window.removeEventListener('mousemove', onMove)
  }, [])

  /* GSAP title reveal sequence */
  useEffect(() => {
    const tl = gsap.timeline({ delay: 0.3 })

    /* Letter-by-letter reveal */
    if (titleRef.current) {
      const letters = titleRef.current.querySelectorAll('.hero-letter')
      tl.fromTo(letters,
        { opacity: 0, y: 30, filter: 'blur(8px)' },
        {
          opacity: 1, y: 0, filter: 'blur(0px)',
          duration: 0.6,
          stagger: 0.06,
          ease: 'expo.out',
        }
      )
    }

    /* Subtitle */
    tl.fromTo(subtitleRef.current,
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.7, ease: 'power3.out' },
      '-=0.2'
    )

    /* Description */
    tl.fromTo(descRef.current,
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' },
      '-=0.3'
    )

    /* CTAs */
    tl.fromTo(ctaRef.current,
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' },
      '-=0.2'
    )

    return () => tl.kill()
  }, [])

  const titleText = 'BAYESTRIP'

  const scrollToSection = (id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section id="hero" className="section" style={{ minHeight: '100vh', padding: 0, justifyContent: 'center' }}>
      {/* 3D Scene behind everything */}
      {tier !== 'low' && (
        <Suspense fallback={null}>
          <HeroScene mouse={mouse} tier={tier} />
        </Suspense>
      )}

      {/* Low-tier fallback gradient */}
      {tier === 'low' && (
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at 50% 40%, rgba(0,240,255,0.08) 0%, transparent 60%), radial-gradient(ellipse at 30% 70%, rgba(168,85,247,0.05) 0%, transparent 50%)',
          zIndex: 0,
        }} />
      )}

      {/* Content overlay */}
      <div style={{
        position: 'relative',
        zIndex: 2,
        textAlign: 'center',
        padding: '0 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px',
      }}>
        {/* Title: letter-by-letter */}
        <h1 ref={titleRef} style={{ marginBottom: 0 }}>
          {titleText.split('').map((char, i) => (
            <span
              key={i}
              className="hero-letter"
              style={{
                display: 'inline-block',
                color: i < 5 ? '#00f0ff' : '#ffa726', /* BAYES in cyan, TRIP in gold */
                textShadow: i < 5
                  ? '0 0 40px rgba(0,240,255,0.3), 0 0 80px rgba(0,240,255,0.1)'
                  : '0 0 40px rgba(255,167,38,0.3), 0 0 80px rgba(255,167,38,0.1)',
                opacity: 0,
              }}
            >
              {char}
            </span>
          ))}
        </h1>

        {/* Subtitle */}
        <div ref={subtitleRef} style={{ opacity: 0 }}>
          <p style={{
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 'clamp(0.6rem, 1.2vw, 0.85rem)',
            fontWeight: 500,
            letterSpacing: '0.25em',
            color: '#8888aa',
            textTransform: 'uppercase',
          }}>
            Intelligent Travel · Powered by Probability
          </p>
        </div>

        {/* Description */}
        <div ref={descRef} style={{ opacity: 0, maxWidth: '520px' }}>
          <p className="subtitle" style={{ fontSize: 'clamp(0.8rem, 1.3vw, 0.95rem)' }}>
            Bayesian Network recommendation + Hidden Markov Model itinerary generation
            for 20 Chennai destinations.
          </p>
        </div>

        {/* CTAs */}
        <div ref={ctaRef} style={{ opacity: 0, display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center', marginTop: '8px' }}>
          <MagneticButton onClick={() => scrollToSection('recommend')}>
            Explore BayesTrip
          </MagneticButton>
          <MagneticButton variant="secondary" onClick={() => scrollToSection('how')}>
            How It Works
          </MagneticButton>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        style={{
          position: 'absolute',
          bottom: '32px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.4 }}
        transition={{ delay: 2.5, duration: 1 }}
      >
        <span style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '0.55rem',
          letterSpacing: '0.15em',
          color: '#8888aa',
          textTransform: 'uppercase',
        }}>
          Scroll
        </span>
        <motion.div
          style={{
            width: '1px',
            height: '30px',
            background: 'linear-gradient(180deg, rgba(0,240,255,0.5), transparent)',
          }}
          animate={{ scaleY: [0, 1, 0] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        />
      </motion.div>
    </section>
  )
}
