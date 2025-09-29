import React from 'react'

const ResultsView = ({ results }) => {
  if (!results) {
    return (
      <div className="card">
        <h2>Results</h2>
        <p>Enter a query to see results</p>
      </div>
    )
  }

  if (results.error) {
    return (
      <div className="card">
        <h2>Error</h2>
        <div style={{ color: '#dc3545', padding: '1rem', background: '#f8d7da', borderRadius: '4px' }}>
          {results.error}
        </div>
      </div>
    )
  }

  const renderTableResults = (data, title) => {
    if (!data || data.length === 0) {
      return <p>No results found</p>
    }

    const columns = Object.keys(data[0])

    return (
      <div style={{ marginBottom: '2rem' }}>
        <h3>{title} ({data.length} results)</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8f9fa' }}>
                {columns.map(column => (
                  <th key={column} style={{ padding: '0.75rem', border: '1px solid #dee2e6', textAlign: 'left' }}>
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={index}>
                  {columns.map(column => (
                    <td key={column} style={{ padding: '0.75rem', border: '1px solid #dee2e6' }}>
                      {String(row[column] || '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const renderDocumentResults = (documents, title) => {
    if (!documents || documents.length === 0) {
      return <p>No document matches found</p>
    }

    return (
      <div style={{ marginBottom: '2rem' }}>
        <h3>{title} ({documents.length} matches)</h3>
        <div style={{ display: 'grid', gap: '1rem' }}>
          {documents.map((doc, index) => (
            <div key={index} className="card" style={{ background: '#f8f9fa' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <strong>Document #{doc.document_id}</strong>
                <span style={{ color: '#007bff' }}>Similarity: {(doc.similarity * 100).toFixed(1)}%</span>
              </div>
              <p style={{ fontSize: '0.9rem', lineHeight: '1.4' }}>{doc.content}</p>
              <div style={{ fontSize: '0.8rem', color: '#6c757d', marginTop: '0.5rem' }}>
                Chunk {doc.chunk_index + 1} • {doc.tokens_count} tokens
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Results</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ 
            padding: '0.25rem 0.5rem', 
            background: '#e7f3ff', 
            borderRadius: '4px',
            fontSize: '0.8rem'
          }}>
            {results.query_type?.toUpperCase()}
          </span>
          <span style={{ fontSize: '0.9rem', color: '#6c757d' }}>
            {results.response_time}s {results.cache_hit && '• 🚀 Cached'}
          </span>
        </div>
      </div>

      {/* SQL Results */}
      {results.results && results.query_type === 'sql' && 
        renderTableResults(results.results, 'Database Results')}

      {/* Document Results */}
      {results.results && results.query_type === 'document' && 
        renderDocumentResults(results.results, 'Document Matches')}

      {/* Hybrid Results */}
      {results.query_type === 'hybrid' && (
        <>
          {renderTableResults(results.sql_results, 'Database Results')}
          {renderDocumentResults(results.document_results, 'Document Matches')}
        </>
      )}

      {/* Generated SQL (for debugging) */}
      {results.sql_generated && (
        <div style={{ marginTop: '2rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
          <h4>Generated SQL:</h4>
          <pre style={{ 
            background: '#2d2d2d', 
            color: '#f8f9fa', 
            padding: '1rem', 
            borderRadius: '4px',
            overflowX: 'auto',
            fontSize: '0.8rem'
          }}>
            {results.sql_generated}
          </pre>
        </div>
      )}

      {/* Export Options */}
      {results.results && results.results.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <button className="btn btn-secondary">
            Export as CSV
          </button>
          <button className="btn btn-secondary" style={{ marginLeft: '0.5rem' }}>
            Export as JSON
          </button>
        </div>
      )}
    </div>
  )
}

export default ResultsView
