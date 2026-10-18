import { useEffect, useState } from 'react'
import { fetchCrops, fetchGoals, submitAnalysis } from './api'
import './App.css'

// Crop options are loaded from the backend (GET /crops): every crop in the
// bundled dataset, displayed as English · Marathi. No hardcoded crop list.
const RAINFALL = ['Yes', 'No', 'Unknown']
const SYMPTOMS = [
  'None',
  'Yellowing Leaves',
  'Leaf Spots',
  'Insects and Leaf Damage',
  'Wilting',
]

// Display metadata for each issue category returned by the backend
const CATEGORY_META = {
  irrigation:    { label: 'Irrigation',          icon: '💧' },
  stress:        { label: 'Heat / Water Stress',  icon: '🌡️' },
  leaf_symptoms: { label: 'Leaf Symptoms',         icon: '🍂' },
  pest:          { label: 'Pest Monitoring',       icon: '🐛' },
  soil_nutrient: { label: 'Soil / Nutrient',       icon: '🌱' },
  dataset:       { label: 'Dataset Reference',     icon: '📊' },
}

// Friendly names for the dataset's numeric columns (dataset_reference panel)
const RANGE_LABELS = {
  N: 'Nitrogen (N)',
  P: 'Phosphorus (P)',
  K: 'Potassium (K)',
  temperature: 'Temperature (°C)',
  humidity: 'Humidity (%)',
  ph: 'Soil pH',
  rainfall: 'Rainfall (mm)',
}

export default function App() {
  const [crops, setCrops] = useState([])
  const [form, setForm] = useState({
    crop: 'rice',
    soil_moisture: 45,
    rainfall: 'No',
    temperature: 28,
    humidity: 60,
    ph: 7,
    symptom: 'None',
    goal: '',
  })
  const [goals, setGoals] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load crops (from the dataset) and backward-chaining goals on first render.
  useEffect(() => {
    fetchCrops()
      .then((data) => {
        setCrops(data.crops)
        // Fall back to the first dataset crop if the default isn't present.
        setForm((f) =>
          data.crops.some((c) => c.label === f.crop)
            ? f
            : { ...f, crop: data.crops[0]?.label ?? f.crop },
        )
      })
      .catch(() => {
        // Non-critical: analyze still works, the select just shows nothing.
        setCrops([])
      })
    fetchGoals()
      .then((data) => {
        setGoals(data.goals)
      })
      .catch(() => {
        // Non-critical: the analyze form still works without goal options.
        setGoals([])
      })
  }, [])

  // Display name for a dataset crop label: "Rice · तांदूळ"
  function cropLabel(label) {
    const found = crops.find((c) => c.label === label)
    return found ? `${found.name_en} · ${found.name_mr}` : label
  }

  function handleChange(e) {
    const { name, value } = e.target
    setForm((f) => ({ ...f, [name]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await submitAnalysis({
        crop: form.crop,
        soil_moisture: Number(form.soil_moisture),
        rainfall: form.rainfall,
        temperature: Number(form.temperature),
        humidity: Number(form.humidity),
        ph: Number(form.ph),
        symptom: form.symptom,
        goal: form.goal || null,
      })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const moistureLabel =
    form.soil_moisture <= 35 ? 'Dry' : form.soil_moisture >= 70 ? 'Wet' : 'Moderate'

  return (
    <div className="app">
      <header className="header">
        <span className="header-icon" aria-hidden="true">🌾</span>
        <div className="header-text">
          <h1>Smart Agriculture Advisory</h1>
          <p className="tagline">Rule-based expert system · forward &amp; backward chaining</p>
        </div>
        <span className="header-badge">AI Lab Mini-Project</span>
      </header>

      <main className="layout">
        {/* ---------------- Input form ---------------- */}
        <section className="card">
          <h2>Field Observations</h2>
          <form onSubmit={handleSubmit}>
            <label>
              Crop type ({crops.length} crops in dataset)
              <select id="crop" name="crop" value={form.crop} onChange={handleChange}>
                {crops.length === 0 && (
                  <option value="">Loading crops…</option>
                )}
                {crops.map((c) => (
                  <option key={c.label} value={c.label}>
                    {c.name_en} · {c.name_mr}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span className="label-row">
                Soil moisture
                <span className={`pill pill-${moistureLabel.toLowerCase()}`}>
                  {form.soil_moisture}% · {moistureLabel}
                </span>
              </span>
              <div className="slider-wrap">
                <input
                  id="soil_moisture"
                  type="range"
                  name="soil_moisture"
                  min="0"
                  max="100"
                  value={form.soil_moisture}
                  onChange={handleChange}
                />
              </div>
              <span className="scale-hint">
                <span>0% dry</span>
                <span>100% saturated</span>
              </span>
            </label>

            <fieldset className="radio-group">
              <legend>Recent rainfall (last ~7 days)</legend>
              <div className="radio-options">
                {RAINFALL.map((r) => (
                  <label key={r} className="radio">
                    <input
                      type="radio"
                      name="rainfall"
                      value={r}
                      checked={form.rainfall === r}
                      onChange={handleChange}
                    />
                    <span className="radio-btn">{r}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <label>
              Temperature (°C)
              <input
                id="temperature"
                type="number"
                name="temperature"
                min="-20"
                max="60"
                step="0.5"
                value={form.temperature}
                onChange={handleChange}
              />
            </label>

            <div className="input-row">
              <label>
                Humidity (%)
                <input
                  id="humidity"
                  type="number"
                  name="humidity"
                  min="0"
                  max="100"
                  step="1"
                  value={form.humidity}
                  onChange={handleChange}
                />
              </label>
              <label>
                Soil pH
                <input
                  id="ph"
                  type="number"
                  name="ph"
                  min="0"
                  max="14"
                  step="0.1"
                  value={form.ph}
                  onChange={handleChange}
                />
              </label>
            </div>
            <p className="field-note">
              Humidity &amp; pH are compared against the dataset's typical
              ranges for the selected crop.
            </p>

            <label>
              Plant symptom
              <select id="symptom" name="symptom" value={form.symptom} onChange={handleChange}>
                {SYMPTOMS.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>

            <label>
              Goal to verify (backward chaining)
              <select id="goal" name="goal" value={form.goal} onChange={handleChange}>
                <option value="">Skip backward chaining</option>
                {goals.map((g) => (
                  <option key={g.fact} value={g.fact}>
                    {g.label}
                  </option>
                ))}
              </select>
            </label>

            <button type="submit" id="analyze-btn" disabled={loading}>
              {loading ? '⏳ Analyzing…' : '🔍 Analyze'}
            </button>
          </form>
        </section>

        {/* ---------------- Results ---------------- */}
        <section className="card results">
          <h2>Advisory Results</h2>

          {error && (
            <div className="state error" role="alert">
              <strong>⚠ Request failed.</strong> {error}
              <p className="hint">
                Is the backend running? Start it with:{' '}
                <code>cd backend &amp;&amp; uvicorn app.main:app --reload</code>
              </p>
            </div>
          )}

          {loading && (
            <div className="state loading" role="status">
              <div className="spinner" />
              Running the rule engine…
            </div>
          )}

          {!loading && !error && !result && (
            <div className="state idle">
              <span className="idle-icon" aria-hidden="true">🛰️</span>
              <p>
                Fill in the field observations and press <strong>Analyze</strong> to run
                the expert system.
              </p>
            </div>
          )}

          {result && !loading && (
            <>
              {/* Stats summary row */}
              <div className="stats-row">
                <span className="stat-chip">📋 {result.rules_evaluated} rules</span>
                <span className="stat-chip">🔥 {result.fired_rule_ids.length} fired</span>
                <span className="stat-chip">🧠 {result.inferred_facts.length} inferred</span>
              </div>

              {/* Verdict banner */}
              <div className={`banner banner-${result.summary.status}`}>
                <span className="banner-icon" aria-hidden="true">
                  {result.summary.status === 'attention'
                    ? '⚠️'
                    : result.summary.status === 'monitor'
                      ? '👀'
                      : '✅'}
                </span>
                <div>
                  <strong>{result.summary.headline}</strong>
                  <p>{result.summary.detail}</p>
                </div>
              </div>

              {/* Dataset reference panel */}
              {result.dataset_reference && result.dataset_reference.available && (
                <div className="block dataset-panel">
                  <h3>
                    📊 Dataset reference · {cropLabel(result.dataset_reference.crop)}
                    <span className={`ref-source ref-${result.dataset_reference.source}`}>
                      {result.dataset_reference.source === 'crop'
                        ? `${result.dataset_reference.rows_for_crop} rows in dataset`
                        : 'all-crop fallback (crop not in dataset)'}
                    </span>
                  </h3>

                  {result.dataset_reference.deviations.length > 0 ? (
                    <ul className="deviations">
                      {result.dataset_reference.deviations.map((d) => (
                        <li key={d}>⚠ {d}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted small">
                      All readings are within the typical range for this crop.
                    </p>
                  )}

                  <table className="ref-table">
                    <thead>
                      <tr>
                        <th>Measurement</th>
                        <th>Typical range (p10–p90)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(result.dataset_reference.typical_ranges).map(
                        ([metric, rng]) => (
                          <tr key={metric}>
                            <td>{RANGE_LABELS[metric] || metric}</td>
                            <td>
                              {rng.p10} – {rng.p90}
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                  <p className="muted small">
                    Ranges are 10th–90th percentiles of the bundled CSV -
                    descriptive statistics, not a trained model.
                  </p>
                </div>
              )}

              {/* Possible issues, grouped by category */}
              {result.conclusions.length === 0 ? (
                <p className="state idle slim">
                  No issue rules triggered — conditions look normal for now. Keep
                  monitoring.
                </p>
              ) : (
                <div className="block">
                  <h3>Possible issues ({result.conclusions.length})</h3>
                  <ul className="issues">
                    {result.conclusions.map((c) => {
                      const meta = CATEGORY_META[c.category] || {
                        label: c.category,
                        icon: '🔎',
                      }
                      return (
                        <li key={c.issue}>
                          <span className="issue-head">
                            <span className="issue-cat">{meta.icon} {meta.label}</span>
                            <span className="issue-text">{c.issue}</span>
                          </span>
                          <span className="rule-tag">
                            from rules {c.source_rules.join(', ')}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              )}

              {result.recommendations.length > 0 && (
                <div className="block">
                  <h3>Recommendations ({result.recommendations.length})</h3>
                  <ul className="recs">
                    {result.recommendations.map((r) => (
                      <li key={r.advice}>
                        <span className="rec-text">{r.advice}</span>
                        <span className="rule-tag">
                          from rules {r.source_rules.join(', ')}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="block">
                <h3>Triggered rules</h3>
                <p className="rule-ids">
                  {result.fired_rule_ids.length > 0
                    ? result.fired_rule_ids.map((id) => (
                        <span key={id} className="rule-chip">{id}</span>
                      ))
                    : <span className="muted">None</span>}
                </p>
              </div>

              <div className="block">
                <h3>Inferred facts</h3>
                <div className="facts">
                  {result.inferred_facts.length > 0
                    ? result.inferred_facts.map((f) => (
                        <span key={f} className="fact-chip">
                          {f}
                        </span>
                      ))
                    : <span className="muted">None beyond the raw inputs</span>}
                </div>
              </div>

              {result.backward_chain && (
                <div className="block">
                  <h3>Backward chaining · goal check</h3>
                  <p className="goal-line">
                    <code>{result.backward_chain.goal}</code>
                    <span
                      className={
                        'goal-badge ' +
                        (result.backward_chain.supported ? 'yes' : 'no')
                      }
                    >
                      {result.backward_chain.supported
                        ? '✓ Supported'
                        : '✗ Not supported'}
                    </span>
                  </p>
                  <ol className="proof">
                    {result.backward_chain.proof.map((line, i) => (
                      <li key={i}>{line}</li>
                    ))}
                  </ol>
                </div>
              )}

              <details className="block trace-block">
                <summary>
                  How the engine reasoned ({result.reasoning_trace.length} steps)
                </summary>
                <ol className="trace">
                  {result.reasoning_trace.map((line, i) => (
                    <li key={i} className={line.startsWith('    ') ? 'sub' : ''}>
                      {line.trim()}
                    </li>
                  ))}
                </ol>
              </details>

              <p className="disclaimer">{result.note}</p>
            </>
          )}
        </section>
      </main>

      <footer className="footer">
        College AI Lab mini-project · rule-based expert system (no ML, no database)
      </footer>
    </div>
  )
}
