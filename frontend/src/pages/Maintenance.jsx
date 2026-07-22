import { useState, useEffect } from 'react'

/**
 * Maintenance Intelligence page — equipment failure cards + Gemini-powered RCA analysis.
 */
export default function Maintenance() {
  const [equipment, setEquipment] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [advanced, setAdvanced] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    fetchEquipment()
  }, [])

  async function fetchEquipment() {
    try {
      const res = await fetch('/api/maintenance/equipment')
      if (!res.ok) throw new Error('Failed to load equipment data')
      const data = await res.json()
      setEquipment(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function analyzeEquipment(equipmentId) {
    setSelectedId(equipmentId)
    setAnalyzing(true)
    setAnalysis(null)
    setAdvanced(null)
    setTimeline([])

    try {
      const [analysisRes, timelineRes, advancedRes] = await Promise.all([
        fetch(`/api/maintenance/analyze/${encodeURIComponent(equipmentId)}`),
        fetch(`/api/maintenance/timeline/${encodeURIComponent(equipmentId)}`),
        fetch(`/api/maintenance/advanced-analysis/${encodeURIComponent(equipmentId)}`)
      ])

      if (!analysisRes.ok) throw new Error('Analysis failed')
      const data = await analysisRes.json()
      setAnalysis(data)

      if (timelineRes.ok) {
        const timelineData = await timelineRes.json()
        setTimeline(timelineData)
      }

      if (advancedRes.ok) {
        const advancedData = await advancedRes.json()
        setAdvanced(advancedData)
      }
    } catch (err) {
      setAnalysis({
        equipment_id: equipmentId,
        predictive_flag: 'Error',
        risk_level: 'Unknown',
        root_cause_analysis: `Analysis failed: ${err.message}`,
        recommended_actions: ['Retry the analysis', 'Check backend logs'],
        next_predicted_failure: 'Unknown',
        confidence: 'Low',
        failure_history: [],
      })
    } finally {
      setAnalyzing(false)
    }
  }

  const flagColors = {
    Yes: 'rose',
    No: 'emerald',
    Watch: 'amber',
    Error: 'rose',
  }

  const riskColors = {
    High: 'rose',
    Medium: 'amber',
    Low: 'emerald',
    Unknown: 'violet',
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>Maintenance Intelligence</h2>
          <p>AI-powered equipment failure analysis and predictive maintenance</p>
        </div>
        <div className="loading-overlay">
          <div className="spinner"></div>
          Loading equipment data...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h2>Maintenance Intelligence</h2>
          <p>AI-powered equipment failure analysis and predictive maintenance</p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <p style={{ color: 'var(--accent-rose)', marginBottom: '12px' }}>⚠ {error}</p>
          <button className="btn btn-secondary" onClick={() => { setLoading(true); setError(null); fetchEquipment(); }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>Maintenance Intelligence</h2>
        <p>AI-powered equipment failure analysis and predictive maintenance</p>
      </div>

      {/* ── Equipment Cards ── */}
      <div className="equipment-grid">
        {equipment.map((eq) => (
          <div
            key={eq.equipment_id}
            className="equipment-card"
            onClick={() => analyzeEquipment(eq.equipment_id)}
            style={{
              borderColor: selectedId === eq.equipment_id ? 'var(--accent-blue)' : undefined,
            }}
          >
            <div className="equipment-card-header">
              <div className="equipment-id">{eq.equipment_id}</div>
              <span className="badge blue" style={{ fontSize: '11px' }}>
                Click to Analyze
              </span>
            </div>

            <div className="equipment-stats">
              <div className="equipment-stat">
                <div className="equipment-stat-value" style={{ color: 'var(--accent-rose)' }}>
                  {eq.total_failures}
                </div>
                <div className="equipment-stat-label">Failures</div>
              </div>
              <div className="equipment-stat">
                <div className="equipment-stat-value" style={{ color: 'var(--accent-amber)' }}>
                  {eq.total_downtime_hours}h
                </div>
                <div className="equipment-stat-label">Total Downtime</div>
              </div>
            </div>

            <div className="equipment-last-failure">
              Last failure: {eq.last_failure_date || 'N/A'}
              {eq.last_failure_type && (
                <span style={{ display: 'block', marginTop: '2px', color: 'var(--text-secondary)' }}>
                  {eq.last_failure_type}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ── Analysis Panel ── */}
      {analyzing && (
        <div className="analysis-panel">
          <div className="loading-overlay">
            <div className="spinner"></div>
            Analyzing {selectedId} with AI...
          </div>
        </div>
      )}

      {analysis && !analyzing && (
        <div className="analysis-panel">
          <div className="analysis-header">
            <div>
              <div className="analysis-title">🔍 Analysis: {analysis.equipment_id}</div>
              <div className="text-sm text-muted mt-8">
                AI-generated insights based on failure history and maintenance documents
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="analysis-flags">
                <span className={`badge ${flagColors[analysis.predictive_flag] || 'amber'}`}>
                  {analysis.predictive_flag === 'Yes' ? '⚠️' : analysis.predictive_flag === 'No' ? '✅' : '👀'}
                  {' '}Predictive: {analysis.predictive_flag}
                </span>
                <span className={`badge ${riskColors[analysis.risk_level] || 'amber'}`}>
                  Risk: {analysis.risk_level}
                </span>
                <span className={`badge ${riskColors[analysis.confidence] || 'violet'}`}>
                  Confidence: {analysis.confidence}
                </span>
              </div>
              <button className="close-btn" onClick={() => { setAnalysis(null); setSelectedId(null); }}>
                ✕
              </button>
            </div>
          </div>

          {/* Root Cause Analysis */}
          <div className="analysis-section">
            <h4>Root Cause Analysis</h4>
            <p>{analysis.root_cause_analysis}</p>
          </div>

          {/* Next Predicted Failure */}
          <div className="analysis-section">
            <h4>Next Predicted Failure</h4>
            <p>{analysis.next_predicted_failure}</p>
          </div>

          {/* Recommended Actions */}
          <div className="analysis-section">
            <h4>Recommended Actions</h4>
            <ul className="analysis-actions-list">
              {analysis.recommended_actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ul>
          </div>

          {/* Advanced AI Recommendations */}
          {advanced && (
            <div className="card" style={{ marginBottom: '24px', background: 'rgba(59, 130, 246, 0.03)', borderColor: 'var(--border-accent)', padding: '20px' }}>
              <h4 style={{ fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--accent-blue-light)', marginBottom: '16px' }}>
                🧠 Advanced AI Reliability Recommendation
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Failure Probability (90d)</div>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: advanced.failure_probability > 50 ? 'var(--accent-rose)' : 'var(--accent-emerald)', marginTop: '4px' }}>
                    {advanced.failure_probability}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Suggested Spares</div>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
                    {advanced.suggested_spares && advanced.suggested_spares.length > 0 ? (
                      advanced.suggested_spares.map((spare, idx) => (
                        <span key={idx} className="badge blue" style={{ fontSize: '10px' }}>{spare}</span>
                      ))
                    ) : (
                      <span className="text-muted text-sm" style={{ fontSize: '12px' }}>No spares flagged</span>
                    )}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>Recommended Schedule</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500, marginTop: '6px' }}>
                    {advanced.recommended_schedule}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                <strong>Recommendation Rationale:</strong> {advanced.rationale}
              </div>
            </div>
          )}

          {/* Equipment Knowledge Timeline */}
          {timeline && timeline.length > 0 && (
            <div style={{ marginBottom: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
              <h4 style={{ fontSize: '13px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-tertiary)', marginBottom: '16px' }}>
                📅 Equipment Knowledge Timeline
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', paddingLeft: '20px', borderLeft: '2px solid var(--bg-tertiary)' }}>
                {timeline.map((event, idx) => (
                  <div key={idx} style={{ position: 'relative' }}>
                    {/* Event Dot */}
                    <div style={{
                      position: 'absolute',
                      left: '-27px',
                      top: '4px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: event.severity === 'High' ? 'var(--accent-rose)' : event.severity === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-blue-light)',
                      border: '3px solid var(--bg-primary)'
                    }}></div>
                    
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontWeight: 600 }}>
                      {event.date} · <span style={{ color: 'var(--accent-cyan)' }}>{event.event_type}</span>
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {event.title}
                    </div>
                    <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.5' }}>
                      {event.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failure History Table */}
          {analysis.failure_history && analysis.failure_history.length > 0 && (
            <div className="failure-history">
              <h4 style={{
                fontSize: '13px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.8px',
                color: 'var(--text-tertiary)',
                marginBottom: '12px',
              }}>
                Failure History
              </h4>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Root Cause</th>
                      <th>Downtime</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.failure_history.map((f, i) => (
                      <tr key={i}>
                        <td>{f.failure_date}</td>
                        <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{f.failure_type}</td>
                        <td>{f.root_cause}</td>
                        <td>
                          <span className="badge amber">{f.downtime_hours}h</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
