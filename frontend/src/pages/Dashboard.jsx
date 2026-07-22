import { useState, useEffect } from 'react'

/**
 * Dashboard — overview stats + recent documents table.
 */
export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboard()
  }, [])

  async function fetchDashboard() {
    try {
      const res = await fetch('/api/dashboard/stats')
      if (!res.ok) throw new Error('Failed to load dashboard')
      const json = await res.json()
      setData(json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>Dashboard</h2>
          <p>Platform overview and recent activity</p>
        </div>
        <div className="loading-overlay">
          <div className="spinner"></div>
          Loading dashboard...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h2>Dashboard</h2>
          <p>Platform overview and recent activity</p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <p style={{ color: 'var(--accent-rose)', marginBottom: '12px' }}>⚠ {error}</p>
          <button className="btn btn-secondary" onClick={() => { setLoading(true); setError(null); fetchDashboard(); }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  const { stats, recent_documents, high_risk_equipment, upcoming_inspections } = data

  const complianceColor = stats.avg_compliance_score >= 90 ? 'emerald' : stats.avg_compliance_score >= 75 ? 'amber' : 'rose'

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Operations Brain platform overview and safety diagnostics</p>
      </div>

      {/* ── Stats Cards ── */}
      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-icon blue">📄</div>
          <div className="stat-value">{stats.total_documents}</div>
          <div className="stat-label">Documents Ingested</div>
        </div>
        <div className="stat-card violet">
          <div className="stat-icon violet">🕸️</div>
          <div className="stat-value">{stats.graph_relationships}</div>
          <div className="stat-label">Graph Relationships</div>
        </div>
        <div className={`stat-card ${complianceColor}`}>
          <div className={`stat-icon ${complianceColor}`}>🦺</div>
          <div className="stat-value">{stats.avg_compliance_score}%</div>
          <div className="stat-label">Compliance Index</div>
        </div>
        <div className="stat-card blue">
          <div className="stat-icon blue">🏷</div>
          <div className="stat-value">{stats.total_entities}</div>
          <div className="stat-label">Entities Tracked</div>
        </div>
      </div>

      {/* ── Mid-level Widgets Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        
        {/* High Risk Equipment Widget */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">⚠️ High-Risk Equipment</h3>
          </div>
          {high_risk_equipment.length === 0 ? (
            <p className="text-muted text-sm" style={{ padding: '16px 0' }}>No high risk equipment flagged.</p>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Equipment</th>
                    <th>Failures</th>
                    <th>Downtime</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {high_risk_equipment.map((eq) => (
                    <tr key={eq.equipment_id}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{eq.equipment_id}</td>
                      <td>{eq.failures}</td>
                      <td>{eq.downtime_hours}h</td>
                      <td>
                        <span className={`badge ${eq.risk_status === 'High' ? 'rose' : 'amber'}`}>
                          {eq.risk_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Upcoming Inspections Widget */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📅 Upcoming Safety Tasks</h3>
          </div>
          {upcoming_inspections.length === 0 ? (
            <p className="text-muted text-sm" style={{ padding: '16px 0' }}>No inspections scheduled.</p>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Equipment</th>
                    <th>Inspection Task</th>
                    <th>Due Date</th>
                  </tr>
                </thead>
                <tbody>
                  {upcoming_inspections.map((insp, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{insp.equipment_id}</td>
                      <td className="text-sm">{insp.type}</td>
                      <td className="text-muted text-sm">{insp.due_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>

      {/* ── Recent Documents ── */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Recently Ingested Documents</h3>
          <span className="card-subtitle">{recent_documents.length} documents total</span>
        </div>

        {recent_documents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-tertiary)' }}>
            <p>No documents yet. Head to the Upload page to get started.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Type</th>
                  <th>Chunks</th>
                  <th>Entities</th>
                  <th>Ingested</th>
                </tr>
              </thead>
              <tbody>
                {recent_documents.map((doc) => (
                  <tr key={doc.id}>
                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                      {doc.filename}
                    </td>
                    <td>
                      <span className={`doc-type-badge ${doc.doc_type}`}>
                        {formatDocType(doc.doc_type)}
                      </span>
                    </td>
                    <td>{doc.chunk_count}</td>
                    <td>
                      <span className="badge violet">{doc.entity_count}</span>
                    </td>
                    <td className="text-muted text-sm">
                      {formatDate(doc.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function formatDocType(type) {
  if (!type) return 'Unknown'
  return type
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}
