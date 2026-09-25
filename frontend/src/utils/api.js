const API_BASE = '/api'

async function request(url, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `API error ${res.status}`)
    }
    return await res.json()
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Connection interrupted — BayesTrip intelligence engine could not be reached.')
    }
    throw err
  }
}

/** Fetch evidence variable options from the backend. */
export async function fetchOptions() {
  return request('/options')
}

/** Fetch all 20 places with coordinates. */
export async function fetchPlaces() {
  return request('/places')
}

/**
 * Run the recommendation pipeline.
 * @param {{ age: string, budget: string, interest: string, travel_type: string, weather: string }} evidence
 * @returns {Promise<{ top5: Array, itinerary: Array }>}
 */
export async function fetchRecommendation(evidence) {
  return request('/recommend', {
    method: 'POST',
    body: JSON.stringify(evidence),
  })
}
