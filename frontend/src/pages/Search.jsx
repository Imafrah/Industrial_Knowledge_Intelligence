import { useState } from 'react'

/**
 * Search page — Hybrid Search combining vector semantic matching
 * and lexical keyword matching via Reciprocal Rank Fusion.
 */
export default function Search() {
  const [query, setQuery] = useState('')
  const [docType, setDocType] = useState('')
  const [equipmentTag, setEquipmentTag] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const docTypes = [
    { value: '', label: 'All Document Types' },
    { value: 'maintenance_procedure', label: 'Maintenance Procedures' },
    { value: 'safety_inspection', label: 'Safety Inspections' },
    { value: 'equipment_manual', label: 'Equipment Manuals' },
    { value: 'incident_report', label: 'Incident Reports' },
    { value: 'regulatory_checklist', label: 'Compliance Checklists' },
  ]

  async function handleSearch(e) {
    if (e) e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const res = await fetch('/api/search/hybrid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          doc_type: docType || null,
          equipment_tag: equipmentTag || null,
          limit: 10
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Search request failed')
      }

      const data = await res.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function highlightQuery(text, query) {
    if (!query) return text
    const parts = query.split(/\s+/).filter(Boolean)
    if (parts.length === 0) return text
    
    // Create regex matching any of the query terms
    const regex = new RegExp(`(${parts.join('|')})`, 'gi')
    const splitText = text.split(regex)
    
    return splitText.map((part, i) => 
      regex.test(part) ? <mark key={i} style={{ backgroundColor: 'rgba(245, 158, 11, 0.3)', color: 'var(--text-primary)', padding: '0 2px', borderRadius: '2px' }}>{part}</mark> : part
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>Hybrid Search Engine</h2>
        <p>Lexical + Semantic search with Reciprocal Rank Fusion (RRF) and metadata filters</p>
      </div>

      {/* ── Search Form & Filters ── */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <form onSubmit={handleSearch}>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
            <div style={{ flex: 1, minWidth: '280px' }}>
              <input
                type="text"
                placeholder="Enter keywords or natural language questions..."
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
              {loading ? <span className="spinner" style={{ width: '16px', height: '16px' }}></span> : 'Search'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {/* Document Type Filter */}
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase' }}>
                Document Type
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  outline: 'none',
                }}
              >
                {docTypes.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* Equipment Tag Filter */}
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase' }}>
                Equipment Tag
              </label>
              <input
                type="text"
                placeholder="e.g. P-101A, HX-201"
                value={equipmentTag}
                onChange={(e) => setEquipmentTag(e.target.value)}
                style={{ padding: '9px 14px' }}
              />
            </div>
          </div>
        </form>
      </div>

      {/* ── Search Metrics Explanation ── */}
      <div className="card" style={{ marginBottom: '24px', background: 'rgba(59, 130, 246, 0.03)', borderColor: 'var(--border-accent)' }}>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span style={{ fontSize: '16px' }}>💡</span>
          <div>
            <strong>Reciprocal Rank Fusion (RRF) Active:</strong> RRF merges lexical keyword matching (Exact)
            and vector embeddings similarity (Semantic) to score results. Best of both worlds.
          </div>
        </div>
      </div>

      {/* ── Results ── */}
      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          Fusing lexical and semantic search pools...
        </div>
      )}

      {error && (
        <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--accent-rose)' }}>
          ⚠ {error}
        </div>
      )}

      {results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Search Results ({results.length})
          </h3>
          {results.map((res) => (
            <div key={res.chunk_id} className="card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px', gap: '12px' }}>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                    📄 {res.filename}
                  </h4>
                  <span className={`doc-type-badge ${res.doc_type || 'other'}`} style={{ fontSize: '10px' }}>
                    {res.doc_type ? res.doc_type.replace(/_/g, ' ') : 'other'}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span className="badge blue" style={{ fontSize: '10px' }}>
                    {res.search_method}
                  </span>
                  <span className="badge emerald" style={{ fontSize: '10px' }}>
                    Rank #{res.rank}
                  </span>
                  <span className="badge violet" style={{ fontSize: '10px' }}>
                    Score: {res.score}
                  </span>
                </div>
              </div>
              <p style={{ fontSize: '13.5px', color: 'var(--text-secondary)', lineHeight: '1.6', background: 'rgba(0, 0, 0, 0.1)', padding: '12px', borderRadius: 'var(--radius-sm)' }}>
                {highlightQuery(res.content, query)}
              </p>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && query && (
        <div className="card" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
          No records matched the hybrid query. Try clearing your filters.
        </div>
      )}
    </div>
  )
}
