import { useState, useEffect, useRef, useCallback } from 'react'
import { NAV_LINKS } from '../utils/constants'

/**
 * Floating glass navbar with animated active indicator that slides between items.
 */
export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [activeSection, setActiveSection] = useState('hero')
  const [indicatorStyle, setIndicatorStyle] = useState({})
  const linksRef = useRef({})

  /* Detect scroll for glass background */
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  /* Intersection observer for active section */
  useEffect(() => {
    const sections = NAV_LINKS.map(l => document.getElementById(l.id)).filter(Boolean)
    if (!sections.length) return

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id)
          }
        }
      },
      { rootMargin: '-40% 0px -40% 0px', threshold: 0 }
    )

    sections.forEach(s => observer.observe(s))
    return () => observer.disconnect()
  }, [])

  /* Move indicator to active link */
  useEffect(() => {
    const el = linksRef.current[activeSection]
    if (el) {
      const parent = el.parentElement
      const parentRect = parent.getBoundingClientRect()
      const elRect = el.getBoundingClientRect()
      setIndicatorStyle({
        left: elRect.left - parentRect.left,
        width: elRect.width,
        top: 0,
      })
    }
  }, [activeSection])

  const scrollTo = useCallback((id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }, [])

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-logo">BAYESTRIP</div>
      <div className="navbar-links">
        <div className="navbar-indicator" style={indicatorStyle} />
        {NAV_LINKS.map(link => (
          <button
            key={link.id}
            ref={el => { linksRef.current[link.id] = el }}
            className={`navbar-link ${activeSection === link.id ? 'active' : ''}`}
            onClick={() => scrollTo(link.id)}
          >
            {link.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
