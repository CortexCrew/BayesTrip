import { useRef, useMemo } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Float } from '@react-three/drei'
import * as THREE from 'three'
import PostProcessing from './PostProcessing'
import { BN_EVIDENCE_NODES, BN_DEST_NODES, COLORS } from '../utils/constants'

/* ── Network Node ────────────────────────────────────────────── */
function NetworkNode({ position, color, radius = 0.09, pulseSpeed = 1 }) {
  const meshRef = useRef()
  const glowRef = useRef()

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()
    const pulse = 1 + Math.sin(t * pulseSpeed + position[0]) * 0.12
    meshRef.current.scale.setScalar(pulse)
    meshRef.current.position.y = position[1] + Math.sin(t * 0.6 + position[0] * 0.5) * 0.08
  })

  return (
    <group position={position}>
      <mesh ref={meshRef}>
        <sphereGeometry args={[radius, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={1.2}
          toneMapped={false}
          roughness={0.3}
          metalness={0.6}
        />
      </mesh>
      {/* Outer glow sphere */}
      <mesh ref={glowRef} scale={2.5}>
        <sphereGeometry args={[radius, 12, 12]} />
        <meshBasicMaterial color={color} transparent opacity={0.06} toneMapped={false} />
      </mesh>
    </group>
  )
}

/* ── Network Edge ────────────────────────────────────────────── */
function NetworkEdge({ start, end, color, opacity = 0.18 }) {
  const geometry = useMemo(() => {
    const pts = [new THREE.Vector3(...start), new THREE.Vector3(...end)]
    return new THREE.BufferGeometry().setFromPoints(pts)
  }, [start, end])

  return (
    <line geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={opacity} toneMapped={false} />
    </line>
  )
}

/* ── Data Pulse (travelling particle along an edge) ──────────── */
function DataPulse({ start, end, color, speed = 0.4, delay = 0 }) {
  const ref = useRef()

  useFrame(({ clock }) => {
    const t = ((clock.getElapsedTime() * speed + delay) % 1)
    ref.current.position.lerpVectors(
      new THREE.Vector3(...start),
      new THREE.Vector3(...end),
      t
    )
    ref.current.material.opacity = Math.sin(t * Math.PI) * 0.9
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.03, 8, 8]} />
      <meshBasicMaterial color={color} transparent opacity={0} toneMapped={false} />
    </mesh>
  )
}

/* ── Floating Particles ──────────────────────────────────────── */
function Particles({ count = 800, spread = 14 }) {
  const ref = useRef()
  const [positions, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3)
    const sz = new Float32Array(count)
    for (let i = 0; i < count; i++) {
      pos[i * 3]     = (Math.random() - 0.5) * spread
      pos[i * 3 + 1] = (Math.random() - 0.5) * spread
      pos[i * 3 + 2] = (Math.random() - 0.5) * spread
      sz[i] = Math.random() * 0.015 + 0.005
    }
    return [pos, sz]
  }, [count, spread])

  useFrame(({ clock }) => {
    ref.current.rotation.y = clock.getElapsedTime() * 0.015
    ref.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.008) * 0.04
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
        <bufferAttribute attach="attributes-size" count={count} array={sizes} itemSize={1} />
      </bufferGeometry>
      <pointsMaterial
        color={COLORS.cyan}
        size={0.025}
        transparent
        opacity={0.45}
        sizeAttenuation
        toneMapped={false}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

/* ── Mouse-Responsive Camera Rig ─────────────────────────────── */
function CameraRig({ mouse }) {
  const { camera } = useThree()
  const target = useRef(new THREE.Vector3(0, 0, 8))

  useFrame(() => {
    /* Smooth follow mouse for subtle parallax */
    const tx = (mouse.current?.x || 0) * 0.8
    const ty = (mouse.current?.y || 0) * 0.5
    target.current.x += (tx - target.current.x) * 0.03
    target.current.y += (ty - target.current.y) * 0.03

    camera.position.x = target.current.x
    camera.position.y = target.current.y
    camera.lookAt(0, 0, 0)
  })

  return null
}

/* ── Main Scene ──────────────────────────────────────────────── */
function Scene({ mouse, tier }) {
  const groupRef = useRef()
  const particleCount = tier === 'high' ? 800 : tier === 'mid' ? 350 : 100

  /* Build edges: every evidence node → every destination node */
  const edges = useMemo(() => {
    const arr = []
    BN_EVIDENCE_NODES.forEach(ev => {
      BN_DEST_NODES.forEach(dest => {
        arr.push({
          start: [ev.x, ev.y, ev.z],
          end:   [dest.x, dest.y, dest.z],
        })
      })
    })
    return arr
  }, [])

  /* A few animated data pulses along random edges */
  const pulses = useMemo(() => {
    const picked = []
    for (let i = 0; i < 8; i++) {
      const ev = BN_EVIDENCE_NODES[Math.floor(Math.random() * BN_EVIDENCE_NODES.length)]
      const dest = BN_DEST_NODES[Math.floor(Math.random() * BN_DEST_NODES.length)]
      picked.push({
        start: [ev.x, ev.y, ev.z],
        end:   [dest.x, dest.y, dest.z],
        delay: Math.random() * 5,
        speed: 0.2 + Math.random() * 0.3,
      })
    }
    return picked
  }, [])

  useFrame(({ clock }) => {
    groupRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.08) * 0.15
  })

  return (
    <>
      {/* Lighting: 3-point studio setup */}
      <ambientLight intensity={0.15} />
      <directionalLight position={[5, 5, 5]}  intensity={0.6} color="#ffffff" />   {/* Key */}
      <directionalLight position={[-5, 2, -3]} intensity={0.3} color="#4488ff" />  {/* Fill */}
      <pointLight       position={[0, -3, 5]}  intensity={0.8} color="#00f0ff" />  {/* Rim */}
      <pointLight       position={[3, 4, -2]}  intensity={0.4} color="#a855f7" />

      <CameraRig mouse={mouse} />

      <Float speed={0.8} rotationIntensity={0.1} floatIntensity={0.3}>
        <group ref={groupRef}>
          {/* Evidence nodes (cyan) */}
          {BN_EVIDENCE_NODES.map(n => (
            <NetworkNode
              key={n.id}
              position={[n.x, n.y, n.z]}
              color={COLORS.cyan}
              radius={0.1}
              pulseSpeed={0.8 + Math.random() * 0.4}
            />
          ))}

          {/* Destination nodes (purple/gold blend) */}
          {BN_DEST_NODES.map(n => (
            <NetworkNode
              key={n.id}
              position={[n.x, n.y, n.z]}
              color={COLORS.purple}
              radius={0.08}
              pulseSpeed={0.6 + Math.random() * 0.3}
            />
          ))}

          {/* Edges */}
          {edges.map((e, i) => (
            <NetworkEdge
              key={i}
              start={e.start}
              end={e.end}
              color={COLORS.cyan}
              opacity={0.1}
            />
          ))}

          {/* Data pulses */}
          {pulses.map((p, i) => (
            <DataPulse
              key={i}
              start={p.start}
              end={p.end}
              color={COLORS.cyan}
              speed={p.speed}
              delay={p.delay}
            />
          ))}
        </group>
      </Float>

      {/* Background particles */}
      <Particles count={particleCount} />

      {/* Post-processing */}
      <PostProcessing tier={tier} />
    </>
  )
}

/* ── Exported Canvas ─────────────────────────────────────────── */
export default function HeroScene({ mouse, tier = 'high' }) {
  return (
    <Canvas
      camera={{ position: [0, 0, 8], fov: 50, near: 0.1, far: 100 }}
      dpr={[1, tier === 'high' ? 2 : 1.5]}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      style={{ position: 'absolute', inset: 0, zIndex: 0 }}
    >
      <Scene mouse={mouse} tier={tier} />
    </Canvas>
  )
}
