import { useState, useEffect } from 'react'

/**
 * Compliance Dashboard — displays regulatory safety compliance scores,
 * severity gap lists, missing procedures, and recommended corrective actions.
 */
export default function Compliance() {
  const [summary, setSummary] = useState(null)
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchComplianceData()
  }, [])

  async function fetchComplianceData() {
    try {
      const [sumRes, findRes] = await Promise.all([
        fetch('/api/compliance/summary'),
        fetch('/api/compliance/findings')
      ])

      if (!sumRes.ok || !findRes.ok) throw new Error('Failed to load compliance records')

      const sumData = await sumRes.json()
      const findData = await findRes.json()

      setSummary(sumData)
      setFindings(findData)
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
          <h2>Safety & Regulatory Compliance</h2>
          <p>AI Audit against Factory Act, OISD, PESO, and Environmental standards</p>
        </div>
        <div className="loading-overlay">
          <div className="spinner"></div>
          Analyzing compliance certificates and audit reports...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h2>Safety & Regulatory Compliance</h2>
          <p>AI Audit against Factory Act, OISD, PESO, and Environmental standards</p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
          <p style={{ color: 'var(--accent-rose)', marginBottom: '12px' }}>⚠ {error}</p>
          <button className="btn btn-secondary" onClick={() => { setLoading(true); setError(null); fetchComplianceData(); }}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  const scoreColor = summary.average_score >= 90 ? 'var(--accent-emerald)' : summary.average_score >= 75 ? 'var(--accent-amber)' : 'var(--accent-rose)'
  const statusColor = summary.status.includes('REQUIRED') || summary.status.includes('WARNING') ? 'var(--accent-rose)' : 'var(--accent-emerald)'

  return (
    <div>
      <div className="page-header">
        <h2>Safety & Regulatory Compliance</h2>
        <p>AI Audit against Factory Act, OISD, and PESO regulations</p>
      </div>

      {/* ── Summary Stats ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Gauge Card */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{
            width: '100px',
            height: '100px',
            borderRadius: '50%',
            border: `8px solid ${scoreColor}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            fontWeight: 800,
            color: scoreColor,
            flexShrink: 0
          }}>
            {summary.average_score}%
          </div>
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>Compliance Index</h4>
            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>
              Avg audit score across all safety certificates and procedures
            </p>
          </div>
        </div>

        {/* Global Severity Count */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <h4 style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: 600, textTransform: 'uppercase' }}>
            Open Regulatory Gaps
          </h4>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-rose)' }}>{summary.critical_gaps_count}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>CRITICAL</div>
            </div>
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-rose)' }}>{summary.high_gaps_count}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>HIGH</div>
            </div>
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-amber)' }}>{summary.medium_gaps_count}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>MEDIUM</div>
            </div>
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-secondary)' }}>{summary.low_gaps_count}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>LOW</div>
            </div>
          </div>
        </div>

        {/* Status indicator */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', borderLeft: `4px solid ${statusColor}` }}>
          <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px' }}>
            Audit Health Status
          </span>
          <div style={{ fontSize: '16px', fontWeight: 700, color: statusColor, marginTop: '4px' }}>
            {summary.status}
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '8px' }}>
            Total audited files: {summary.total_audits}
          </p>
        </div>
      </div>

      {/* ── Audited Findings ── */}
      <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' }}>
        Compliance Audit Reports & Gaps
      </h3>

      {findings.length === 0 ? (
        <div className="card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
          No audited documents found. Run safety checklists or upload regulatory checklists to trigger compliance scanning.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {findings.map((f) => (
            <div key={f.id} className="card">
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', paddingBottom: '14px', borderBottom: '1px solid var(--border-color)', marginBottom: '16px' }}>
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    📄 {f.filename}
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
                    Audited Regulation: <span style={{ color: 'var(--accent-blue-light)', fontWeight: 500 }}>{f.regulation_type}</span>
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span className={`badge ${f.severity_level === 'Critical' || f.severity_level === 'High' ? 'rose' : f.severity_level === 'Medium' ? 'amber' : 'emerald'}`}>
                    {f.severity_level} Severity
                  </span>
                  <span className="badge blue" style={{ fontWeight: 700 }}>
                    Score: {f.compliance_score}/100
                  </span>
                </div>
              </div>

              {/* Gap Details */}
              {f.gap_details && (
                <div style={{ marginBottom: '16px' }}>
                  <h5 style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                    Identified Gaps / Non-Compliance
                  </h5>
                  <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                    {f.gap_details}
                  </p>
                </div>
              )}

              {/* Corrective Actions */}
              {f.corrective_actions && f.corrective_actions.length > 0 && (
                <div>
                  <h5 style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                    Recommended Corrective Actions
                  </h5>
                  <ul className="analysis-actions-list">
                    {f.corrective_actions.map((act, i) => (
                      <li key={i}>{act}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
