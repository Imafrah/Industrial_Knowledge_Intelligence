import { useState, useEffect } from 'react'

/**
 * Lessons Learned page — search for historical similar incidents,
 * root causes, and resolutions using vector-powered incident lookup.
 */
export default function Lessons() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeIncident, setActiveIncident] = useState(null)
  const [equipmentList, setEquipmentList] = useState([])

  useEffect(() => {
    // Collect unique equipment items from maintenance routes to show in dropdown
    fetchEquipment()
  }, [])

  async function fetchEquipment() {
    try {
      const res = await fetch('/api/maintenance/equipment')
      if (res.ok) {
        const data = await res.json()
        setEquipmentList(data.map(d => d.equipment_id))
      }
    } catch (err) {
      console.error(err)
    }
  }

  async function handleSearch(e) {
    if (e) e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResults([])
    setActiveIncident(null)

    try {
      // We will perform hybrid search over incident reports
      const res = await fetch('/api/search/hybrid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          doc_type: 'incident_report',
          limit: 5
        })
      })

      if (!res.ok) throw new Error('Search failed')
      const data = await res.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function queryIncidentRCA(equipmentId) {
    setLoading(true)
    setError(null)
    setResults([])
    setActiveIncident(null)
    setQuery(equipmentId)

    try {
      const res = await fetch(`/api/maintenance/analyze/${encodeURIComponent(equipmentId)}`)
      if (!res.ok) throw new Error('Analysis failed')
      const data = await res.json()
      setActiveIncident(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Lessons Learned Engine</h2>
        <p>Retrieve similar historical incidents, root causes, and corrective actions from past logs</p>
      </div>

      {/* ── Search Bar ── */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <form onSubmit={handleSearch}>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
            <div style={{ flex: 1, minWidth: '280px' }}>
              <input
                type="text"
                placeholder="Search historical incidents (e.g. 'impeller cavitation', 'seal blowout', or equipment ID)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{ height: '48px', fontSize: '15px' }}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ height: '48px', padding: '0 24px' }}
              disabled={loading || !query.trim()}
            >
              {loading ? <span className="spinner" style={{ width: '16px', height: '16px' }}></span> : 'Search logs'}
            </button>
          </div>

          {/* Quick Equipment Select */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
              Quick Lookup by Equipment:
            </span>
            {equipmentList.map((eq) => (
              <button
                key={eq}
                type="button"
                className="suggested-question"
                style={{ margin: 0, padding: '4px 12px', fontSize: '11.5px' }}
                onClick={() => queryIncidentRCA(eq)}
              >
                {eq} History
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* ── Results Panel ── */}
      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          Searching historical databases and vector embeddings...
        </div>
      )}

      {error && (
        <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--accent-rose)', marginBottom: '24px' }}>
          ⚠ {error}
        </div>
      )}

      {/* RAG Active Incident Display */}
      {activeIncident && !loading && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px', animation: 'panelSlideIn 0.3s ease-out' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '14px', borderBottom: '1px solid var(--border-color)' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                🚨 Historical Diagnostics: {activeIncident.equipment_id}
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
                AI-compiled incident analysis & failure loop resolutions
              </p>
            </div>
            <span className={`badge ${activeIncident.risk_level === 'High' ? 'rose' : 'amber'}`}>
              Risk: {activeIncident.risk_level}
            </span>
          </div>

          <div className="analysis-section">
            <h4 style={{ color: 'var(--accent-cyan)' }}>Likely Root Cause Patterns</h4>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: '1.6' }}>
              {activeIncident.root_cause_analysis}
            </p>
          </div>

          <div className="analysis-section">
            <h4 style={{ color: 'var(--accent-emerald)' }}>Resolutions & Actions</h4>
            <ul className="analysis-actions-list" style={{ marginTop: '8px' }}>
              {activeIncident.recommended_actions.map((act, i) => (
                <li key={i}>{act}</li>
              ))}
            </ul>
          </div>

          {/* Failure Records list */}
          {activeIncident.failure_history && activeIncident.failure_history.length > 0 && (
            <div>
              <h4 style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>
                Incident Logs
              </h4>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Incident Type</th>
                      <th>Root Cause</th>
                      <th>Downtime</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeIncident.failure_history.map((f, i) => (
                      <tr key={i}>
                        <td style={{ fontSize: '12.5px' }}>{f.failure_date}</td>
                        <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{f.failure_type}</td>
                        <td style={{ fontSize: '13px' }}>{f.root_cause}</td>
                        <td><span className="badge rose">{f.downtime_hours}h</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Semantic Search Results Display */}
      {results.length > 0 && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Found Matches in Incident Logs
          </h3>
          {results.map((res) => (
            <div key={res.chunk_id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  📄 {res.filename}
                </h4>
                <span className="badge blue">{res.search_method}</span>
              </div>
              <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.6', background: 'rgba(0, 0, 0, 0.1)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                {res.content}
              </p>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !activeIncident && !loading && (
        <div className="card" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
          🔍 Search for equipment histories or keyword descriptors to fetch incident diagnostics.
        </div>
      )}
    </div>
  )
}
