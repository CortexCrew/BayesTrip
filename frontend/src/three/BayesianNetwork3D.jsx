import { useRef, useMemo, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Html } from '@react-three/drei'
import * as THREE from 'three'
import { COLORS } from '../utils/constants'

/* ── Interactive Node ────────────────────────────────────────── */
function BNNode({ position, label, color, active, radius = 0.18, onClick, labelOffset = -30 }) {
  const ref = useRef()
  const [hovered, setHovered] = useState(false)

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime()
    const s = active ? 1.3 : hovered ? 1.15 : 1.0
    const pulse = 1 + Math.sin(t * 1.5 + position[0]) * (active ? 0.08 : 0.04)
    ref.current.scale.setScalar(s * pulse)
  })

  return (
    <group position={position}>
      <mesh
        ref={ref}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[radius, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={active ? 2 : hovered ? 1.2 : 0.6}
          toneMapped={false}
          roughness={0.3}
          metalness={0.5}
        />
      </mesh>
      {/* Glow */}
      <mesh scale={active ? 2.5 : 2}>
        <sphereGeometry args={[radius, 8, 8]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={active ? 0.15 : 0.05}
          toneMapped={false}
        />
      </mesh>
      {/* Label */}
      <Html center distanceFactor={8} style={{ pointerEvents: 'none' }}>
        <div style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: '0.55rem',
          fontWeight: 600,
          letterSpacing: '0.08em',
          color: active ? color : '#8888aa',
          textShadow: active ? `0 0 10px ${color}` : 'none',
          whiteSpace: 'nowrap',
          userSelect: 'none',
          transform: `translateY(${labelOffset}px)`,
        }}>
          {label}
        </div>
      </Html>
    </group>
  )
}

/* ── Edge ─────────────────────────────────────────────────────── */
function BNEdge({ from, to, active }) {
  const geometry = useMemo(() => {
    return new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(...from),
      new THREE.Vector3(...to),
    ])
  }, [from, to])

  return (
    <line geometry={geometry}>
      <lineBasicMaterial
        color={active ? COLORS.cyan : '#334455'}
        transparent
        opacity={active ? 0.4 : 0.08}
        toneMapped={false}
      />
    </line>
  )
}

/* ── Animated Pulse Along Edge ───────────────────────────────── */
function EdgePulse({ from, to, speed = 0.3, delay = 0 }) {
  const ref = useRef()

  useFrame(({ clock }) => {
    const t = ((clock.getElapsedTime() * speed + delay) % 1)
    ref.current.position.lerpVectors(
      new THREE.Vector3(...from),
      new THREE.Vector3(...to),
      t
    )
    ref.current.material.opacity = Math.sin(t * Math.PI) * 0.8
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.035, 8, 8]} />
      <meshBasicMaterial color={COLORS.cyan} transparent opacity={0} toneMapped={false} />
    </mesh>
  )
}

/* ── Main Network ────────────────────────────────────────────── */
function Network({ activeNodes = [] }) {
  const groupRef = useRef()

  const evidenceNodes = [
    { id: 'age',         label: 'AGE',         pos: [-2.8, 2.2, 0], labelOffset: -35 },
    { id: 'budget',      label: 'BUDGET',      pos: [-1.4, 2.5, 0.3], labelOffset: -35 },
    { id: 'interest',    label: 'INTEREST',    pos: [0, 2.7, 0], labelOffset: -35 },
    { id: 'travel_type', label: 'TRAVEL TYPE', pos: [1.4, 2.5, 0.3], labelOffset: -35 },
    { id: 'weather',     label: 'WEATHER',     pos: [2.8, 2.2, 0], labelOffset: -35 },
  ]

  const destNodes = [
    { id: 'place', label: 'P(PLACE | E)', pos: [0, 0, 0], labelOffset: -45 },
  ]

  /* Secondary destination fan */
  const subDests = [
    { id: 'd1', label: 'D₁', pos: [-2.5, -2.0, 0.2], labelOffset: 30 },
    { id: 'd2', label: 'D₂', pos: [-1.2, -2.2, -0.3], labelOffset: 30 },
    { id: 'd3', label: 'D₃', pos: [0,    -2.0, 0.4], labelOffset: 30 },
    { id: 'd4', label: 'D₄', pos: [1.2,  -2.2, -0.2], labelOffset: 30 },
    { id: 'd5', label: 'D₅', pos: [2.5,  -2.0, 0.1], labelOffset: 30 },
  ]

  useFrame(({ clock }) => {
    groupRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.06) * 0.12
  })

  return (
    <Float speed={0.5} rotationIntensity={0.05} floatIntensity={0.2}>
      <group ref={groupRef}>
        {/* Evidence → Central node edges */}
        {evidenceNodes.map(ev => (
          <BNEdge
            key={`e-${ev.id}`}
            from={ev.pos}
            to={destNodes[0].pos}
            active={activeNodes.includes(ev.id)}
          />
        ))}

        {/* Central → Sub-destination edges */}
        {subDests.map(d => (
          <BNEdge key={`d-${d.id}`} from={destNodes[0].pos} to={d.pos} active={activeNodes.length > 0} />
        ))}

        {/* Pulses on active edges */}
        {evidenceNodes
          .filter(ev => activeNodes.includes(ev.id))
          .map((ev, i) => (
            <EdgePulse
              key={`p-${ev.id}`}
              from={ev.pos}
              to={destNodes[0].pos}
              speed={0.25}
              delay={i * 1.2}
            />
          ))
        }

        {/* Evidence nodes */}
        {evidenceNodes.map(n => (
          <BNNode
            key={n.id}
            position={n.pos}
            label={n.label}
            color={COLORS.cyan}
            active={activeNodes.includes(n.id)}
            radius={0.16}
            labelOffset={n.labelOffset}
          />
        ))}

        {/* Central posterior node */}
        <BNNode
          position={destNodes[0].pos}
          label={destNodes[0].label}
          color={COLORS.purple}
          active={activeNodes.length > 0}
          radius={0.22}
          labelOffset={destNodes[0].labelOffset}
        />

        {/* Sub-destination nodes */}
        {subDests.map(d => (
          <BNNode
            key={d.id}
            position={d.pos}
            label={d.label}
            color={COLORS.gold}
            active={activeNodes.length > 0}
            radius={0.1}
            labelOffset={d.labelOffset}
          />
        ))}
      </group>
    </Float>
  )
}

/* ── Exported Component ──────────────────────────────────────── */
export default function BayesianNetwork3D({ activeNodes = [], className = '' }) {
  return (
    <div className={className} style={{ width: '100%', height: '400px', position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 0.5, 9], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ borderRadius: '16px' }}
      >
        <ambientLight intensity={0.15} />
        <directionalLight position={[5, 5, 5]} intensity={0.5} />
        <pointLight position={[0, 0, 4]} intensity={0.6} color={COLORS.cyan} />
        <Network activeNodes={activeNodes} />
      </Canvas>
    </div>
  )
}
