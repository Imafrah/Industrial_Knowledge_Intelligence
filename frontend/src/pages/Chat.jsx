import { useState, useRef, useEffect } from 'react'

/**
 * Chat page — RAG-powered Q&A with citations and confidence scoring.
 */
export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const messagesEndRef = useRef(null)

  const suggestedQuestions = [
    'What is the maintenance procedure for pump P-101A?',
    'What safety issues were found in the latest inspection?',
    'What caused the near-miss incident with steam tracing?',
    'What are the operating parameters for heat exchanger HX-201?',
    'What regulatory compliance items are due next quarter?',
    'What happened during the reactor R-201 temperature excursion?',
  ]

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  async function sendMessage(questionText) {
    const question = (questionText || input).trim()
    if (!question || thinking) return

    // Add user message
    const userMsg = { role: 'user', content: question }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setThinking(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Request failed (${res.status})`)
      }

      const data = await res.json()
      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        confidence: data.confidence,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message}`,
        sources: [],
        confidence: 'Low',
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setThinking(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const confidenceBadgeClass = {
    High: 'emerald',
    Medium: 'amber',
    Low: 'rose',
  }

  return (
    <div>
      <div className="page-header">
        <h2>Knowledge Copilot</h2>
        <p>Ask questions about your industrial documents — powered by RAG + Gemini</p>
      </div>

      <div className="chat-container">
        {/* ── Messages ── */}
        <div className="chat-messages">
          {messages.length === 0 && !thinking && (
            <div className="chat-empty">
              <div className="chat-empty-icon">🤖</div>
              <h3>Ask me anything about your plant operations</h3>
              <p>
                I can search through your ingested documents — maintenance procedures, safety reports,
                equipment manuals, incident reports — and give you cited answers with confidence scores.
              </p>
              <div className="suggested-questions">
                {suggestedQuestions.map((q, i) => (
                  <button
                    key={i}
                    className="suggested-question"
                    onClick={() => sendMessage(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <MessageBubble
              key={idx}
              message={msg}
              confidenceBadgeClass={confidenceBadgeClass}
            />
          ))}

          {thinking && (
            <div className="thinking-indicator">
              <div className="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="thinking-text">Searching & analyzing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ── Input ── */}
        <div className="chat-input-area">
          <div className="chat-input-wrapper">
            <input
              type="text"
              placeholder="Ask a question about your documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={thinking}
            />
            <button
              className="btn btn-primary"
              onClick={() => sendMessage()}
              disabled={!input.trim() || thinking}
            >
              {thinking ? (
                <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
              ) : (
                'Send'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Individual message bubble with collapsible sources.
 */
function MessageBubble({ message, confidenceBadgeClass }) {
  const [showSources, setShowSources] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="message user">
        <div className="message-bubble">{message.content}</div>
      </div>
    )
  }

  return (
    <div className="message assistant">
      <div className="message-bubble">
        {/* Render answer with basic line breaks */}
        {message.content.split('\n').map((line, i) => (
          <span key={i}>
            {line}
            {i < message.content.split('\n').length - 1 && <br />}
          </span>
        ))}

        {/* Confidence + Sources toggle */}
        {message.sources && message.sources.length > 0 && (
          <>
            <div className="message-meta">
              <span className={`badge ${confidenceBadgeClass[message.confidence] || 'rose'}`}>
                {message.confidence === 'High' ? '🟢' : message.confidence === 'Medium' ? '🟡' : '🔴'}{' '}
                {message.confidence} Confidence
              </span>
            </div>

            <button
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              📎 {message.sources.length} Source{message.sources.length !== 1 ? 's' : ''}{' '}
              {showSources ? '▲' : '▼'}
            </button>

            {showSources && (
              <div className="sources-list">
                {message.sources.map((src, i) => (
                  <div key={i} className="source-item">
                    <div className="source-item-header">
                      <span className="source-filename">📄 {src.filename}</span>
                      <span className="source-similarity">
                        {(src.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <div className="source-excerpt">{src.excerpt}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
