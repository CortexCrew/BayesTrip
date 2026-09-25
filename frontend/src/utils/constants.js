/* Evidence variable options — mirrored from the backend, used for immediate render
   before /api/options responds. The backend is the source of truth. */
export const EVIDENCE_OPTIONS = {
  age: ['Student', 'Adult'],
  budget: ['Low', 'Medium', 'High'],
  interest: ['History', 'Nature', 'Spiritual', 'Shopping', 'Entertainment'],
  travel_type: ['Solo', 'Friends', 'Family'],
  weather: ['Sunny', 'Rainy'],
}

/* Icons for each evidence option (emoji fallback — no extra icon lib needed) */
export const OPTION_ICONS = {
  Student: '🎓', Adult: '💼',
  Low: '💰', Medium: '💳', High: '💎',
  History: '🏛️', Nature: '🌿', Spiritual: '🕉️', Shopping: '🛍️', Entertainment: '🎭',
  Solo: '🧭', Friends: '👥', Family: '👨‍👩‍👧‍👦',
  Sunny: '☀️', Rainy: '🌧️',
}

/* Labels for evidence groups */
export const EVIDENCE_LABELS = {
  age: 'Age Group',
  budget: 'Budget',
  interest: 'Interest',
  travel_type: 'Travel Type',
  weather: 'Weather',
}

/* 3D Bayesian Network graph layout — evidence nodes feed into a hidden layer */
export const BN_EVIDENCE_NODES = [
  { id: 'age',         label: 'Age',         x: -4,  y: 2.5, z: 0 },
  { id: 'budget',      label: 'Budget',      x: -2,  y: 2.5, z: 0.5 },
  { id: 'interest',    label: 'Interest',    x:  0,  y: 3,   z: 0 },
  { id: 'travel_type', label: 'Travel',      x:  2,  y: 2.5, z: 0.5 },
  { id: 'weather',     label: 'Weather',     x:  4,  y: 2.5, z: 0 },
]

export const BN_DEST_NODES = [
  { id: 'd1', label: 'P(D₁)', x: -3.5, y: -1.5, z: 0.3 },
  { id: 'd2', label: 'P(D₂)', x: -1.8, y: -2,   z: -0.4 },
  { id: 'd3', label: 'P(D₃)', x:  0,   y: -1.5, z: 0.5 },
  { id: 'd4', label: 'P(D₄)', x:  1.8, y: -2,   z: -0.3 },
  { id: 'd5', label: 'P(D₅)', x:  3.5, y: -1.5, z: 0.2 },
]

/* Computation sequence messages (shown during API call) */
export const COMPUTATION_STEPS = [
  'Collecting evidence vectors...',
  'Computing posterior P(Place | Evidence)...',
  'Ranking destination probabilities...',
  'Initializing HMM state space...',
  'Running Viterbi decoding...',
  'Optimizing itinerary sequence...',
  'System ready.',
]

/* Loading screen initialization steps */
export const LOADING_STEPS = [
  'Loading Bayesian Network...',
  'Loading destination database...',
  'Initializing HMM engine...',
  'Loading visual engine...',
  'Establishing route intelligence...',
]

/* Color constants (match CSS vars) */
export const COLORS = {
  cyan:    '#00f0ff',
  cyanDim: '#00a8b3',
  gold:    '#ffa726',
  goldDim: '#cc8520',
  purple:  '#a855f7',
  bgPrimary:   '#0a0a0f',
  bgSecondary: '#12121a',
  textPrimary:   '#e8e8e8',
  textSecondary: '#8888aa',
}

/* Nav links */
export const NAV_LINKS = [
  { id: 'hero',       label: 'Home' },
  { id: 'how',        label: 'How It Works' },
  { id: 'recommend',  label: 'Recommend' },
  { id: 'results',    label: 'Results' },
  { id: 'about',      label: 'About' },
]
