import { useState, useEffect, useCallback } from 'react'
import Lenis from 'lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

import { useGPUTier } from './hooks/useGPUTier'
import { useReducedMotion } from './hooks/useReducedMotion'

import CursorFollower from './components/CursorFollower'
import LoadingScreen from './components/LoadingScreen'
import Navbar from './components/Navbar'

import Hero from './sections/Hero'
import HowItWorks from './sections/HowItWorks'
import Recommender from './sections/Recommender'
import Results from './sections/Results'
import About from './sections/About'

gsap.registerPlugin(ScrollTrigger)

export default function App() {
  const [loading, setLoading] = useState(true)
  const [results, setResults] = useState(null)
  const tier = useGPUTier()
  const reduced = useReducedMotion()

  /* Effective tier: downgrade if reduced motion */
  const effectiveTier = reduced ? 'low' : tier

  /* Initialize Lenis smooth scroll */
  useEffect(() => {
    if (reduced) return // Use native scroll for reduced motion

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      smoothWheel: true,
    })

    /* Connect Lenis to GSAP ScrollTrigger */
    lenis.on('scroll', ScrollTrigger.update)

    gsap.ticker.add((time) => {
      lenis.raf(time * 1000)
    })
    gsap.ticker.lagSmoothing(0)

    return () => {
      lenis.destroy()
      gsap.ticker.remove(lenis.raf)
    }
  }, [reduced])

  const onLoadComplete = useCallback(() => {
    setLoading(false)
  }, [])

  const onResults = useCallback((data) => {
    setResults(data)
  }, [])

  return (
    <>
      {/* Custom cursor (hidden on touch/reduced-motion) */}
      <CursorFollower />

      {/* Cinematic loading screen */}
      {loading && <LoadingScreen onComplete={onLoadComplete} />}

      {/* Global atmosphere overlays */}
      {!reduced && <div className="film-grain" />}
      <div className="vignette-overlay" />

      {/* Navigation */}
      {!loading && <Navbar />}

      {/* Main content */}
      <main style={{ opacity: loading ? 0 : 1, transition: 'opacity 0.6s ease' }}>
        <Hero tier={effectiveTier} />
        <HowItWorks tier={effectiveTier} />
        <Recommender onResults={onResults} />
        <Results data={results} />
        <About />
      </main>
    </>
  )
}
