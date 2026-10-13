import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { MapContainer, TileLayer, Marker, Popup, Polyline, ZoomControl, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
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

function createRouteIcon(number, type, selected) {
  return L.divIcon({
    className: 'bayestrip-marker-shell',
    html: `<span class="route-marker route-marker--${type}${selected ? ' is-selected' : ''}">${number}</span>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  })
}

/* ── Map controls and route framing ──────────────────────────── */
function FitBounds({ positions }) {
  const map = useMap()
  const boundsKey = positions.map(point => point.join(',')).join(';')

  useEffect(() => {
    if (positions.length > 0) {
      map.fitBounds(L.latLngBounds(positions), {
        paddingTopLeft: [32, 142],
        paddingBottomRight: [32, 48],
        maxZoom: 14,
        animate: true,
      })
    }
  }, [boundsKey, map])
  return null
}

function ResetView({ positions }) {
  const map = useMap()
  const boundsKey = positions.map(point => point.join(',')).join(';')

  return (
    <button
      type="button"
      className="map-reset-button"
      aria-label="Reset map to show the full route"
      title="Reset route view"
      onClick={() => {
        if (positions.length > 0) {
          map.fitBounds(L.latLngBounds(positions), {
            paddingTopLeft: [32, 142],
            paddingBottomRight: [32, 48],
            maxZoom: 14,
            animate: true,
          })
        }
      }}
    >
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <path d="M4 8a6.5 6.5 0 1 1-.1 4M4 4v4h4" />
      </svg>
    </button>
  )
}

function FlyTo({ lat, lng }) {
  const map = useMap()
  useEffect(() => {
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      map.flyTo([lat, lng], 15, { duration: 0.8 })
    }
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
    const allPositions = data.itinerary.filter(
      stop => Number.isFinite(Number(stop.lat)) && Number.isFinite(Number(stop.lng))
    )
    setRouteData(null)
    setSelectedPlace(null)
    if (allPositions.length < 2) {
      setRouteLoading(false)
      setRouteError(true)
      return
    }

    const controller = new AbortController()
    setRouteLoading(true)
    setRouteError(null)

    // OSRM expects: lon,lat;lon,lat
    const coords = allPositions.map(p => `${p.lng},${p.lat}`).join(';')
    const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`

    fetch(url, { signal: controller.signal })
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
        if (err.name !== 'AbortError') {
          console.error('OSRM Routing Error:', err)
          setRouteError(true)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setRouteLoading(false)
      })

    return () => controller.abort()
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
  const allPositions = itinerary.filter(
    stop => Number.isFinite(Number(stop.lat)) && Number.isFinite(Number(stop.lng))
  )
  const fitPositions = routeData?.path || allPositions.map(stop => [stop.lat, stop.lng])

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
      <div className="route-map-section">
        <div className="section-header" style={{ marginBottom: '16px' }}>
          <div className="section-label">ROUTE MAP</div>
          <h2 className="section-title">Your journey, mapped</h2>
          <p className="section-subtitle">A road-by-road view of your HMM-optimized Chennai itinerary.</p>
        </div>
        <div className="map-container">
          <div className="route-stats" aria-live="polite">
            {routeLoading ? (
              <div className="route-status"><span className="route-status-dot" />Calculating road route…</div>
            ) : routeError ? (
              <div className="route-status route-status--error">Road route unavailable. Stops are still shown.</div>
            ) : routeData && (
              <>
                <div className="route-stat">
                  <span className="route-stat-icon route-stat-icon--stops" aria-hidden="true">
                    <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="6.5" /><circle cx="10" cy="10" r="2" /></svg>
                  </span>
                  <span className="route-stat-copy"><span className="route-stat-label">Stops</span><strong>{routeData.stops}</strong></span>
                </div>
                <div className="route-stat">
                  <span className="route-stat-icon" aria-hidden="true">
                    <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="7" /><path d="M10 6v4l2.7 1.8" /></svg>
                  </span>
                  <span className="route-stat-copy"><span className="route-stat-label">Driving time</span><strong>{formatDuration(routeData.duration)}</strong></span>
                </div>
                <div className="route-stat">
                  <span className="route-stat-icon" aria-hidden="true">
                    <svg viewBox="0 0 20 20"><path d="M3 14.5 7.2 5l2.8 6 2-3 5 6.5z" /><path d="M3 16h14" /></svg>
                  </span>
                  <span className="route-stat-copy"><span className="route-stat-label">Distance</span><strong>{formatDistance(routeData.distance)}</strong></span>
                </div>
              </>
            )}
          </div>

          <MapContainer
            center={[13.06, 80.24]}
            zoom={12}
            scrollWheelZoom
            zoomControl={false}
            style={{ width: '100%', height: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <ZoomControl position="topright" />
            <FitBounds positions={fitPositions} />
            <ResetView positions={fitPositions} />
            {selectedPlace && <FlyTo lat={selectedPlace.lat} lng={selectedPlace.lng} />}

            {routeData && (
              <>
                <Polyline
                  positions={routeData.path}
                  pathOptions={{ color: '#1677d2', weight: 10, opacity: 0.16, lineCap: 'round', lineJoin: 'round' }}
                  interactive={false}
                />
                <Polyline
                  positions={routeData.path}
                  pathOptions={{ color: '#1677d2', weight: 5, opacity: 0.94, lineCap: 'round', lineJoin: 'round' }}
                >
                  <Popup>
                    <div className="route-popup">
                      <strong>BayesTrip driving route</strong>
                      <span>{formatDistance(routeData.distance)} · {formatDuration(routeData.duration)}</span>
                    </div>
                  </Popup>
                </Polyline>
              </>
            )}

            {allPositions.map((stop, i) => {
              const type = i === 0 ? 'start' : i === allPositions.length - 1 ? 'finish' : 'stop'
              return (
                <Marker
                  key={stop.place_id}
                  position={[stop.lat, stop.lng]}
                  icon={createRouteIcon(i + 1, type, selectedPlace?.place_id === stop.place_id)}
                  eventHandlers={{ click: () => setSelectedPlace(stop) }}
                >
                <Popup>
                  <div className="route-popup route-popup--stop">
                    <span className={`route-popup-number route-popup-number--${type}`}>{i + 1}</span>
                    <span className="route-popup-copy"><strong>{stop.name}</strong><span>{stop.slot} · {stop.time_range}</span></span>
                  </div>
                </Popup>
                </Marker>
              )
            })}
          </MapContainer>
        </div>
        <div className="map-footer">
          <div className="route-legend" aria-label="Route marker legend">
            <span><i className="legend-line" />OSRM driving route</span>
            <span><i className="legend-marker legend-marker--start">1</i>Start</span>
            <span><i className="legend-marker legend-marker--stop">2</i>Stop</span>
            <span><i className="legend-marker legend-marker--finish">{allPositions.length}</i>Finish</span>
          </div>
          <details className="route-steps">
            <summary>View all {allPositions.length} stops</summary>
            <ol>
              {allPositions.map((stop, i) => (
                <li key={stop.place_id}>
                  <button type="button" onClick={() => setSelectedPlace(stop)}>
                    <span className="route-step-number">{i + 1}</span>
                    <span><strong>{stop.name}</strong><small>{stop.slot} · {stop.time_range}</small></span>
                  </button>
                </li>
              ))}
            </ol>
          </details>
        </div>
      </div>
    </SectionTransition>
  )
}
