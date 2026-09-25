import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import SectionTransition from '../components/SectionTransition'
import GlassCard from '../components/GlassCard'
import MagneticButton from '../components/MagneticButton'
import ParticleField from '../components/ParticleField'

/* ── Utilities ───────────────────────────────────────────────── */
function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h} hr ${m} min`
  return `${m} min`
}

function formatDistance(meters) {
  return (meters / 1000).toFixed(2) + ' km'
}

/* ── Custom map marker ───────────────────────────────────────── */
function createPulsingIcon(color = '#ffa726') {
  return L.divIcon({
    className: '',
    html: `
      <div style="
        width: 14px; height: 14px; background: ${color}; border-radius: 50%;
        box-shadow: 0 0 12px ${color}88, 0 0 24px ${color}44;
        animation: timelinePulse 2s ease-in-out infinite;
      "></div>
    `,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

/* ── Map auto-fit to markers ─────────────────────────────────── */
function FitBounds({ positions }) {
  const map = useMap()
  useEffect(() => {
    if (positions.length > 0) {
      const bounds = L.latLngBounds(positions.map(p => [p.lat, p.lng]))
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
    }
  }, [positions, map])
  return null
}

/* ── FlyTo on selection ──────────────────────────────────────── */
function FlyTo({ lat, lng }) {
  const map = useMap()
  useEffect(() => {
    if (lat && lng) map.flyTo([lat, lng], 15, { duration: 1.2 })
  }, [lat, lng, map])
  return null
}

export default function Results({ data }) {
  const [selectedPlace, setSelectedPlace] = useState(null)
  const [routeData, setRouteData] = useState(null)
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState(null)

  useEffect(() => {
    if (!data || !data.itinerary) return
    const allPositions = data.itinerary.filter(s => s.lat && s.lng)
    if (allPositions.length < 2) return
    
    setRouteLoading(true)
    setRouteError(null)

    // OSRM expects: lon,lat;lon,lat
    const coords = allPositions.map(p => `${p.lng},${p.lat}`).join(';')
    const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error("HTTP error " + res.status)
        return res.json()
      })
      .then(resData => {
        if (resData.code === 'Ok' && resData.routes.length > 0) {
          const route = resData.routes[0]
          // GeoJSON returns [lon, lat], Leaflet Polyline expects [lat, lng]
          const latLngs = route.geometry.coordinates.map(coord => [coord[1], coord[0]])
          setRouteData({
            path: latLngs,
            distance: route.distance, // in meters
            duration: route.duration, // in seconds
            stops: allPositions.length
          })
        } else {
          throw new Error("OSRM could not calculate route")
        }
      })
      .catch(err => {
        console.error("OSRM Routing Error:", err)
        setRouteError(true)
      })
      .finally(() => {
        setRouteLoading(false)
      })
  }, [data]) // Re-run when new trip data comes in

  if (!data) {
    return (
      <SectionTransition id="results" variant="warm">
        <div className="section-header">
          <div className="section-label" style={{ color: '#ffa726' }}>YOUR JOURNEY</div>
          <h2 className="section-title">Results</h2>
        </div>
        <div className="state-message">
          <div className="state-icon">🧭</div>
          <div className="state-title">NO JOURNEY GENERATED</div>
          <div className="state-desc">
            Provide your travel preferences above to activate the recommendation engine.
          </div>
          <MagneticButton onClick={() => {
            document.getElementById('recommend')?.scrollIntoView({ behavior: 'smooth' })
          }}>
            Configure Preferences
          </MagneticButton>
        </div>
      </SectionTransition>
    )
  }

  const { top5, itinerary } = data
  const maxPosterior = Math.max(...top5.map(d => d.posterior))
  const allPositions = itinerary.filter(s => s.lat && s.lng)

  return (
    <SectionTransition id="results" variant="warm">
      {/* Warm atmosphere background */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(ellipse at 50% 30%, rgba(255,167,38,0.06) 0%, transparent 60%), radial-gradient(ellipse at 70% 80%, rgba(168,85,247,0.04) 0%, transparent 50%)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />
      <ParticleField
        count={20}
        color="rgba(255,167,38,0.25)"
        connectionColor="rgba(255,167,38,0.05)"
        connectionDistance={100}
      />

      <div className="section-header">
        <div className="section-label" style={{ color: '#ffa726' }}>YOUR JOURNEY</div>
        <h2 className="section-title">Top Destinations</h2>
        <p className="section-subtitle">
          Ranked by posterior probability P(Place | Evidence). The AI has spoken.
        </p>
      </div>

      {/* ── Top-5 Cards ──────────────────────────────────────── */}
      <div className="results-grid">
        {top5.map((dest, i) => (
          <motion.div
            key={dest.place_id}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.12, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          >
            <GlassCard
              className="destination-card"
              onClick={() => {
                const itStop = itinerary.find(s => s.place_id === dest.place_id)
                if (itStop) setSelectedPlace(itStop)
              }}
              style={{ cursor: 'pointer' }}
            >
              <div className="rank-badge">{i + 1}</div>
              <div className="dest-name">{dest.name}</div>
              <div className="dest-category">{dest.place_id}</div>
              <div className="prob-bar-track">
                <motion.div
                  className="prob-bar-fill"
                  initial={{ width: 0 }}
                  whileInView={{ width: `${(dest.posterior / maxPosterior) * 100}%` }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.12 + 0.3, duration: 1, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
              <div className="prob-value">
                {(dest.posterior * 100).toFixed(1)}%
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* ── Itinerary Timeline ───────────────────────────────── */}
      <div style={{ marginTop: '64px' }}>
        <div className="section-header">
          <div className="section-label" style={{ color: '#ffa726' }}>OPTIMIZED SEQUENCE</div>
          <h2 className="section-title" style={{ fontSize: 'clamp(1.2rem, 2.5vw, 1.8rem)' }}>
            Your Itinerary
          </h2>
          <p className="section-subtitle">
            HMM + Viterbi decoded path across three time slots.
          </p>
        </div>

        <div className="itinerary-timeline">
          {itinerary.map((stop, i) => (
            <motion.div
              key={stop.place_id}
              className="timeline-item"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="timeline-dot" />
              <div className="slot-label">{stop.slot}</div>
              <div className="slot-time">{stop.time_range}</div>
              <div
                className="slot-card"
                onClick={() => setSelectedPlace(stop)}
                style={{ cursor: 'pointer' }}
                role="button"
                tabIndex={0}
              >
                <div style={{
                  fontFamily: "'Orbitron', sans-serif",
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: '#e8e8e8',
                  marginBottom: '4px',
                }}>
                  {stop.name}
                </div>
                <div style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.65rem',
                  color: '#55556a',
                }}>
                  {stop.lat?.toFixed(4)}, {stop.lng?.toFixed(4)}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* ── Interactive Map ──────────────────────────────────── */}
      <div style={{ marginTop: '48px' }}>
        <div className="section-header" style={{ marginBottom: '16px' }}>
          <div className="section-label" style={{ color: '#ffa726' }}>ROUTE MAP</div>
        </div>
        <div className="map-container" style={{ position: 'relative' }}>
          {(routeData || routeLoading || routeError) && (
            <div style={{
              position: 'absolute',
              top: '16px',
              left: '60px',
              zIndex: 1000,
              background: 'rgba(10,10,15,0.85)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255,167,38,0.3)',
              borderRadius: '12px',
              padding: '16px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              pointerEvents: 'none'
            }}>
              {routeLoading && (
                <div style={{ fontFamily: "'Orbitron', sans-serif", color: '#8888aa', fontSize: '0.8rem' }}>
                  ⏳ Calculating route...
                </div>
              )}
              {routeError && (
                <div style={{ fontFamily: "'Orbitron', sans-serif", color: '#ff4444', fontSize: '0.8rem' }}>
                  ❌ Route calculation failed.
                </div>
              )}
              {routeData && !routeLoading && (
                <div style={{ display: 'flex', gap: '24px' }}>
                  <div>
                    <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '0.65rem', color: '#8888aa', letterSpacing: '0.1em', marginBottom: '4px' }}>STOPS</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '1.1rem', color: '#e8e8e8', fontWeight: 600 }}>{routeData.stops}</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '0.65rem', color: '#8888aa', letterSpacing: '0.1em', marginBottom: '4px' }}>DRIVING TIME</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '1.1rem', color: '#ffa726', fontWeight: 600 }}>{formatDuration(routeData.duration)}</div>
                  </div>
                  <div>
                    <div style={{ fontFamily: "'Orbitron', sans-serif", fontSize: '0.65rem', color: '#8888aa', letterSpacing: '0.1em', marginBottom: '4px' }}>DISTANCE</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '1.1rem', color: '#00f0ff', fontWeight: 600 }}>{formatDistance(routeData.distance)}</div>
                  </div>
                </div>
              )}
            </div>
          )}
          <MapContainer
            center={[13.06, 80.24]}
            zoom={12}
            scrollWheelZoom={false}
            style={{ width: '100%', height: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <FitBounds positions={allPositions} />
            {selectedPlace && <FlyTo lat={selectedPlace.lat} lng={selectedPlace.lng} />}

            {/* Route Polyline (OSRM or Fallback) */}
            {routeData ? (
              <>
                <Polyline
                  positions={routeData.path}
                  pathOptions={{ color: '#ffa726', weight: 4, opacity: 0.8 }}
                >
                  <Popup>
                    <div style={{
                      fontFamily: "'Inter', sans-serif",
                      fontSize: '0.8rem',
                      color: '#333',
                    }}>
                      <b>BayesTrip Route</b><br/><br/>
                      🛣️ Distance: {formatDistance(routeData.distance)}<br/>
                      ⏱️ Travel Time: {formatDuration(routeData.duration)}
                    </div>
                  </Popup>
                </Polyline>
                <Polyline
                  positions={routeData.path}
                  pathOptions={{ color: '#ffa726', weight: 12, opacity: 0.2 }}
                />
              </>
            ) : allPositions.length > 1 && (
              <Polyline
                positions={allPositions.map(p => [p.lat, p.lng])}
                pathOptions={{
                  color: '#ffa726',
                  weight: 3,
                  opacity: 0.6,
                  dashArray: '8, 8',
                }}
              />
            )}

            {/* Markers */}
            {itinerary.map((stop, i) => stop.lat && stop.lng && (
              <Marker
                key={stop.place_id}
                position={[stop.lat, stop.lng]}
                icon={createPulsingIcon(
                  selectedPlace?.place_id === stop.place_id ? '#00f0ff' : '#ffa726'
                )}
              >
                <Popup>
                  <div style={{
                    fontFamily: "'Inter', sans-serif",
                    fontSize: '0.8rem',
                    color: '#333',
                  }}>
                    <strong>{stop.name}</strong><br />
                    {stop.slot} · {stop.time_range}
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </div>
    </SectionTransition>
  )
}
