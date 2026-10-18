// Small helper module for talking to the FastAPI backend.
// VITE_API_URL is inlined at build time (Docker images set it via build arg);
// local dev falls back to the uvicorn default.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function handleJson(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    // FastAPI validation errors come back as { detail: [...] }
    let message = `HTTP ${response.status}`
    if (typeof data.detail === 'string') {
      message = data.detail
    } else if (Array.isArray(data.detail)) {
      message = data.detail
        .map((d) => `${(d.loc || []).join('.')}: ${d.msg}`)
        .join('; ')
    }
    throw new Error(message)
  }
  return data
}

/** POST field observations to /analyze. */
export async function submitAnalysis(payload) {
  const response = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleJson(response)
}

/** GET the backward-chaining goal options from /goals. */
export async function fetchGoals() {
  const response = await fetch(`${API_URL}/goals`)
  return handleJson(response)
}

/** GET all crops in the bundled dataset, with English + Marathi names. */
export async function fetchCrops() {
  const response = await fetch(`${API_URL}/crops`)
  return handleJson(response)
}
