import { useState, useEffect } from 'react'

/**
 * Mobile Field Technician Mode — responsive mock layout simulating field operations:
 * bar code scanner, query diagnostics, inspection camera capture, and offline logging.
 */
export default function FieldTech() {
  const [equipmentId, setEquipmentId] = useState('')
  const [history, setHistory] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Camera scanner state mock
  const [scanning, setScanning] = useState(false)
  const [scanMessage, setScanMessage] = useState('')

  // Offline status simulation
  const [online, setOnline] = useState(true)
  const [offlineQueue, setOfflineQueue] = useState([])

  const testEquipments = ['P-101A', 'P-101B', 'HX-201', 'R-201', 'DS-03']

  async function lookupEquipment(eqId) {
    const id = eqId || equipmentId
    if (!id.trim()) return

    setLoading(true)
    setError(null)
    setAnalysis(null)
    setHistory([])

    try {
      if (!online) {
        // Offline simulator
        setScanMessage(`Offline: Enqueued lookup request for ${id}`)
        setOfflineQueue((prev) => [...prev, `Lookup ${id}`])
        setLoading(false)
        return
      }

      // Fetch timeline
      const timelineRes = await fetch(`/api/maintenance/timeline/${encodeURIComponent(id)}`)
      if (!timelineRes.ok) throw new Error('Timeline lookup failed')
      const timelineData = await timelineRes.json()
      setHistory(timelineData)

      // Fetch advanced analysis
      const analysisRes = await fetch(`/api/maintenance/advanced-analysis/${encodeURIComponent(id)}`)
      if (analysisRes.ok) {
        const analysisData = await analysisRes.json()
        setAnalysis(analysisData)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Scan simulation
  function simulateBarcodeScan() {
    setScanning(true)
    setScanMessage('Position barcode / QR code in viewfinder...')

    setTimeout(() => {
      // Pick a random equipment tag
      const randomTag = testEquipments[Math.floor(Math.random() * testEquipments.length)]
      setEquipmentId(randomTag)
      setScanMessage(`✓ Scanned Code successfully: Detected ${randomTag}`)
      setScanning(false)
      lookupEquipment(randomTag)
    }, 2500)
  }

  // Camera photo upload simulation for OCR pipeline
  function handlePhotoUpload(e) {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setScanMessage(`Ingesting photo: "${file.name}" through OCR pipeline...`)

    // Simulate pipeline ingestion delays
    setTimeout(() => {
      setScanMessage(`✓ OCR pipeline completed. Document "${file.name}" added to background compliance audits.`)
      setLoading(false)
    }, 3000)
  }

  function toggleConnection() {
    setOnline(!online)
    if (!online) {
      setScanMessage('Connection restored. Syncing offline cache logs with database...')
      setTimeout(() => {
        setOfflineQueue([])
        setScanMessage('✓ Offline cache synced successfully.')
      }, 2000)
    }
  }

  return (
    <div style={{ maxWidth: '480px', margin: '0 auto', padding: '0 8px' }}>
      {/* Phone container mockup */}
      <div style={{
        background: 'var(--bg-secondary)',
        border: '4px solid var(--bg-tertiary)',
        borderRadius: '24px',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-lg)',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '80vh',
      }}>
        {/* Phone Notch Header */}
        <div style={{
          background: 'var(--bg-sidebar)',
          padding: '12px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '11px',
          fontWeight: 600,
          color: 'var(--text-tertiary)',
          borderBottom: '1px solid var(--border-color)',
        }}>
          <div>📶 5G</div>
          <div style={{ color: 'var(--text-primary)', letterSpacing: '0.5px' }}>FIELD TECHNICIAN WORKSPACE</div>
          <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={toggleConnection}>
            <span style={{ color: online ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>●</span>
            {online ? 'ONLINE' : 'OFFLINE'}
          </div>
        </div>

        {/* Mock Screen Content */}
        <div style={{ padding: '16px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Header Action card */}
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>Unified Asset Access</h3>
            <p style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Field assistant for immediate RCA diagnostics</p>
          </div>

          {/* Scanners & Quick Inputs */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={simulateBarcodeScan}
              disabled={scanning}
              style={{
                flex: 1,
                padding: '12px',
                background: 'rgba(59, 130, 246, 0.12)',
                border: '1px solid var(--border-accent)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--accent-blue-light)',
                fontWeight: 600,
                fontSize: '12.5px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span>📷</span>
              Scan Equipment QR
            </button>
            
            <label style={{
              flex: 1,
              padding: '12px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--accent-emerald)',
              fontWeight: 600,
              fontSize: '12.5px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              textAlign: 'center'
            }}>
              <span>📄</span>
              Scan Document
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>

          {/* Search form */}
          <div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Enter Equipment Tag (e.g. P-101A)"
                value={equipmentId}
                onChange={(e) => setEquipmentId(e.target.value.toUpperCase())}
                style={{ height: '40px', fontSize: '13px', padding: '0 12px' }}
              />
              <button
                className="btn btn-primary"
                onClick={() => lookupEquipment()}
                disabled={loading || !equipmentId.trim()}
                style={{ padding: '0 16px', height: '40px', fontSize: '13px' }}
              >
                Go
              </button>
            </div>
            
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '8px' }}>
              {testEquipments.map((tag) => (
                <button
                  key={tag}
                  className="suggested-question"
                  style={{ fontSize: '10px', padding: '3px 8px', margin: 0 }}
                  onClick={() => { setEquipmentId(tag); lookupEquipment(tag); }}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* Scan Messages / Log events */}
          {scanMessage && (
            <div style={{
              padding: '10px 12px',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11.5px',
              color: 'var(--text-secondary)',
              lineHeight: '1.4'
            }}>
              💡 {scanMessage}
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <span className="spinner" style={{ display: 'inline-block' }}></span>
              <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '8px' }}>Querying mobile workspace API...</p>
            </div>
          )}

          {/* Offline cache warning */}
          {!online && offlineQueue.length > 0 && (
            <div style={{
              padding: '10px 12px',
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              color: 'var(--accent-rose)',
            }}>
              ⚠️ Enqueued offline activities: {offlineQueue.length} items. Restore connection to sync.
            </div>
          )}

          {/* Mobile diagnostic cards */}
          {analysis && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>{analysis.equipment_id} Diagnostics</span>
                  <span className={`badge ${analysis.priority === 'Immediate' || analysis.priority === 'High' ? 'rose' : 'amber'}`} style={{ fontSize: '9.5px', padding: '2px 8px' }}>
                    {analysis.priority} Priority
                  </span>
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)' }}>
                  <strong>Failure Risk:</strong> {analysis.failure_probability}% over next 90 days.
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  <strong>Suggested Spares:</strong> {analysis.suggested_spares.join(', ') || 'None required.'}
                </div>
                <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  <strong>Schedule Check:</strong> {analysis.recommended_schedule}
                </div>
              </div>
            </div>
          )}

          {/* Mobile Timeline events */}
          {history.length > 0 && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <h4 style={{ fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Equipment Log History ({history.length})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {history.map((event, idx) => (
                  <div key={idx} style={{
                    padding: '10px 12px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-sm)',
                    borderLeft: `3px solid ${event.severity === 'High' ? 'var(--accent-rose)' : event.severity === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-blue-light)'}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>
                      <span>{event.date}</span>
                      <strong style={{ textTransform: 'uppercase' }}>{event.event_type}</strong>
                    </div>
                    <div style={{ fontSize: '12.5px', fontWeight: 600, color: 'var(--text-primary)' }}>{event.title}</div>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: '1.4' }}>{event.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state mockup */}
          {!analysis && history.length === 0 && !loading && (
            <div style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-tertiary)', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <p style={{ fontSize: '24px', marginBottom: '8px' }}>🔍</p>
              <p style={{ fontSize: '12px' }}>Use the camera QR scanner above or search an equipment ID to compile field diagnostics.</p>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
