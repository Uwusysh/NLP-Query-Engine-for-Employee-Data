import React, { useState, useEffect } from 'react'
import axios from 'axios'

const QueryPanel = ({ connectionString, onResults }) => {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [suggestions, setSuggestions] = useState([])

  useEffect(() => {
    loadQueryHistory()
  }, [])

  const loadQueryHistory = async () => {
    try {
      const response = await axios.get('/api/query/history?limit=5')
      setHistory(response.data.queries)
    } catch (err) {
      console.error('Failed to load query history')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || !connectionString) return

    setLoading(true)
    
    try {
      const response = await axios.post('/api/query', {
        query: query,
        connection_string: connectionString
      })
      
      onResults(response.data)
      loadQueryHistory() // Refresh history
      
    } catch (err) {
      onResults({
        error: err.response?.data?.detail || 'Query failed',
        results: [],
        results_count: 0
      })
    } finally {
      setLoading(false)
    }
  }

  const handleHistoryClick = (historyQuery) => {
    setQuery(historyQuery)
  }

  // Simple auto-suggestions based on common patterns
  const commonQueries = [
    "How many employees do we have?",
    "Average salary by department",
    "List employees hired this year",
    "Show me Python developers",
    "Employees in Engineering department",
    "Top 5 highest paid employees"
  ]

  return (
    <div className="card">
      <h2>Query Interface</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Enter your question:</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your employee data..."
            rows="3"
            disabled={loading}
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>

        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading || !query.trim() || !connectionString}
        >
          {loading ? <div className="spinner"></div> : 'Search'}
        </button>
      </form>

      {/* Query Suggestions */}
      <div style={{ marginTop: '1rem' }}>
        <h4>Try these queries:</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {commonQueries.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem' }}
              onClick={() => setQuery(suggestion)}
              disabled={loading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Query History */}
      {history.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h4>Recent Queries:</h4>
          {history.map((item) => (
            <div 
              key={item.id}
              style={{
                padding: '0.5rem',
                margin: '0.25rem 0',
                background: '#f8f9fa',
                borderRadius: '4px',
                cursor: 'pointer',
                border: '1px solid #e9ecef'
              }}
              onClick={() => handleHistoryClick(item.query_text)}
            >
              <div style={{ fontWeight: '500' }}>{item.query_text}</div>
              <div style={{ fontSize: '0.8rem', color: '#6c757d' }}>
                {item.query_type} • {item.results_count} results • {item.response_time}s
                {item.cache_hit && ' • 🚀 Cached'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default QueryPanel