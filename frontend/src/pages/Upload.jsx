import { useState, useRef } from 'react'

/**
 * Upload page — drag-and-drop file upload with progress and results display.
 */
export default function Upload() {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState('')
  const [statusType, setStatusType] = useState('') // '', 'success', 'error'
  const [uploadedFiles, setUploadedFiles] = useState([])
  const fileInputRef = useRef(null)

  async function handleFile(file) {
    if (!file) return

    // Validate extension
    const ext = file.name.split('.').pop().toLowerCase()
    const allowed = ['pdf', 'docx', 'xlsx', 'txt', 'text', 'csv']
    if (!allowed.includes(ext)) {
      setStatusText(`Unsupported file type: .${ext}. Allowed: ${allowed.join(', ')}`)
      setStatusType('error')
      return
    }

    setUploading(true)
    setProgress(0)
    setStatusText(`Uploading ${file.name}...`)
    setStatusType('')

    // Simulate progress stages (upload → extract → chunk → embed → entities)
    const stages = [
      { pct: 15, text: `Uploading ${file.name}...` },
      { pct: 30, text: 'Extracting text...' },
      { pct: 50, text: 'Chunking document...' },
      { pct: 70, text: 'Generating embeddings...' },
      { pct: 85, text: 'Extracting entities with AI...' },
    ]

    let stageIdx = 0
    const progressInterval = setInterval(() => {
      if (stageIdx < stages.length) {
        setProgress(stages[stageIdx].pct)
        setStatusText(stages[stageIdx].text)
        stageIdx++
      }
    }, 1200)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Upload failed (${res.status})`)
      }

      const data = await res.json()
      setProgress(100)
      setStatusText(`✓ Successfully ingested "${data.filename}" — ${data.chunk_count} chunks, ${data.entity_count} entities`)
      setStatusType('success')
      setUploadedFiles((prev) => [data, ...prev])
    } catch (err) {
      clearInterval(progressInterval)
      setProgress(0)
      setStatusText(`✗ ${err.message}`)
      setStatusType('error')
    } finally {
      setUploading(false)
    }
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setDragOver(true)
  }

  function handleDragLeave() {
    setDragOver(false)
  }

  function handleFileInput(e) {
    const file = e.target.files[0]
    handleFile(file)
    // Reset input so same file can be uploaded again
    e.target.value = ''
  }

  const docTypeIcons = {
    maintenance_procedure: '🔧',
    safety_inspection: '🦺',
    equipment_manual: '📘',
    incident_report: '⚠️',
    regulatory_checklist: '✅',
    rfi: '📋',
    other: '📄',
  }

  return (
    <div>
      <div className="page-header">
        <h2>Document Upload</h2>
        <p>Ingest industrial documents into the knowledge base</p>
      </div>

      {/* ── Upload Zone ── */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div
          className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="upload-zone-icon">📁</div>
          <h3>Drop files here or click to browse</h3>
          <p>Supports PDF, DOCX, XLSX, and plain text files (max 20 MB)</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.xlsx,.txt,.text,.csv"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />
        </div>

        {/* Progress */}
        {(uploading || statusText) && (
          <div className="upload-progress">
            {uploading && (
              <div className="progress-bar-track">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            )}
            <div className={`upload-status ${statusType}`}>
              {uploading && <span className="spinner" style={{ display: 'inline-block', width: '14px', height: '14px', marginRight: '8px', verticalAlign: 'middle' }}></span>}
              {statusText}
            </div>
          </div>
        )}
      </div>

      {/* ── Ingestion Pipeline Info ── */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">Ingestion Pipeline</h3>
        </div>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {['Extract Text', 'Chunk (~500 tokens)', 'Generate Embeddings', 'Extract Entities', 'Store in Vector DB'].map((step, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                background: 'rgba(59, 130, 246, 0.06)',
                border: '1px solid rgba(59, 130, 246, 0.1)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12.5px',
                color: 'var(--text-secondary)',
              }}
            >
              <span style={{ color: 'var(--accent-blue-light)', fontWeight: 700 }}>{i + 1}</span>
              {step}
              {i < 4 && <span style={{ color: 'var(--text-tertiary)', marginLeft: '4px' }}>→</span>}
            </div>
          ))}
        </div>
      </div>

      {/* ── Uploaded Files History ── */}
      {uploadedFiles.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Uploaded This Session</h3>
            <span className="card-subtitle">{uploadedFiles.length} files</span>
          </div>
          <div className="uploaded-files">
            {uploadedFiles.map((file, idx) => (
              <div key={idx} className="uploaded-file-item">
                <div className="uploaded-file-icon">
                  {docTypeIcons[file.doc_type] || '📄'}
                </div>
                <div className="uploaded-file-info">
                  <div className="uploaded-file-name">{file.filename}</div>
                  <div className="uploaded-file-meta">
                    {file.chunk_count} chunks · {file.entity_count} entities · Type: {formatDocType(file.doc_type)}
                  </div>
                </div>
                <span className="badge emerald">✓ Ingested</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function formatDocType(type) {
  if (!type) return 'Unknown'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
