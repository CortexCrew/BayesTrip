import { Bloom, ChromaticAberration, EffectComposer, Noise, Vignette } from '@react-three/postprocessing'
import { BlendFunction } from 'postprocessing'
import { Vector2 } from 'three'

/**
 * Cinematic post-processing stack — gated by GPU tier.
 * @param {{ tier: 'high'|'mid'|'low' }} props
 */
export default function PostProcessing({ tier = 'high' }) {
  if (tier === 'low') return null

  return (
    <EffectComposer multisampling={0}>
      <Bloom
        intensity={tier === 'high' ? 0.8 : 0.4}
        luminanceThreshold={0.2}
        luminanceSmoothing={0.9}
        mipmapBlur
      />
      {tier === 'high' && (
        <ChromaticAberration
          blendFunction={BlendFunction.NORMAL}
          offset={new Vector2(0.0004, 0.0004)}
          radialModulation={false}
          modulationOffset={0.0}
        />
      )}
      <Noise
        premultiply
        blendFunction={BlendFunction.ADD}
        opacity={tier === 'high' ? 0.04 : 0.02}
      />
      <Vignette
        eskil={false}
        offset={0.1}
        darkness={tier === 'high' ? 0.7 : 0.5}
      />
    </EffectComposer>
  )
}
