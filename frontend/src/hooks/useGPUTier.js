import { useState, useEffect } from 'react'

/**
 * Detect GPU/hardware tier for progressive enhancement.
 * Returns 'high' | 'mid' | 'low'.
 */
export function useGPUTier() {
  const [tier, setTier] = useState('mid')

  useEffect(() => {
    const cores = navigator.hardwareConcurrency || 2
    const mobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)
    const touchOnly = matchMedia('(hover: none) and (pointer: coarse)').matches

    if (mobile || touchOnly || cores < 2) {
      setTier('low')
    } else if (cores >= 4) {
      /* Try WebGL renderer info for a rough GPU check */
      try {
        const canvas = document.createElement('canvas')
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
        if (gl) {
          const dbg = gl.getExtension('WEBGL_debug_renderer_info')
          const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : ''
          /* Low-end integrated GPUs */
          if (/SwiftShader|Intel.*HD|Mesa/i.test(renderer)) {
            setTier('mid')
          } else {
            setTier('high')
          }
        } else {
          setTier('mid')
        }
      } catch {
        setTier('mid')
      }
    } else {
      setTier('mid')
    }
  }, [])

  return tier
}
