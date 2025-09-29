import React, { useState } from 'react'
import axios from 'axios'

const DatabaseConnector = ({ onSchemaDiscovered, connectionString, onConnectionStringChange }) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [schema, setSchema] = useState(null)
  const [debugInfo, setDebugInfo] = useState('')

  const testConnection = async () => {
    if (!connectionString) {
      setError('Please enter a connection string')
      return
    }

    setLoading(true)
    setError('')
    setDebugInfo('Connecting...')

    try {
      const formData = new FormData()
      formData.append('connection_string', connectionString)

      const response = await axios.post('/api/ingest/database', formData)
      
      setSchema(response.data.schema)
      onSchemaDiscovered(response.data.schema)
      setDebugInfo(`Connected successfully to: ${response.data.schema.database_info?.name || 'unknown database'}`)
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Connection failed'
      setError(errorMsg)
      setDebugInfo(`Error: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const visualizeSchema = async () => {
    if (!connectionString) return

    try {
      const response = await axios.get('/api/schema/visualize', {
        params: { connection_string: connectionString }
      })
      console.log('Schema visualization data:', response.data)
      alert('Check browser console for schema visualization data')
    } catch (err) {
      setError('Failed to visualize schema')
    }
  }

  const createSampleData = async () => {
    if (!connectionString) return

    setLoading(true)
    try {
      // This would call a new endpoint to create sample data
      // For now, we'll just inform the user
      setDebugInfo('Please run the debug_database.py script to create sample tables')
    } catch (err) {
      setError('Failed to create sample data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>Database Connection</h2>
      
      <div className="form-group">
        <label>Database Connection String:</label>
        <input
          type="text"
          value={connectionString}
          onChange={(e) => onConnectionStringChange(e.target.value)}
          placeholder="postgresql://user:pass@localhost/company_db"
          disabled={loading}
          style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
        />
        <small style={{ color: '#6c757d' }}>
          Examples: postgresql://user:pass@localhost/dbname, mysql://user:pass@localhost/dbname
        </small>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <button 
          className="btn btn-primary" 
          onClick={testConnection}
          disabled={loading}
        >
          {loading ? <div className="spinner"></div> : 'Connect & Analyze'}
        </button>
        
        {schema && (
          <button 
            className="btn btn-secondary" 
            onClick={visualizeSchema}
          >
            Visualize Schema
          </button>
        )}
        
        {schema && schema.tables_count === 0 && (
          <button 
            className="btn btn-warning" 
            onClick={createSampleData}
            style={{ background: '#ffc107', color: '#000' }}
          >
            Create Sample Data
          </button>
        )}
      </div>

      {debugInfo && (
        <div style={{ 
          padding: '0.75rem', 
          background: '#e7f3ff', 
          borderRadius: '4px',
          marginBottom: '1rem',
          fontFamily: 'monospace',
          fontSize: '0.9rem'
        }}>
          {debugInfo}
        </div>
      )}

      {error && (
        <div style={{ 
          color: '#dc3545', 
          padding: '0.75rem', 
          background: '#f8d7da', 
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          {error}
        </div>
      )}

      {schema && (
        <div style={{ 
          marginTop: '1rem', 
          padding: '1rem', 
          background: schema.tables_count > 0 ? '#d4edda' : '#fff3cd',
          borderRadius: '4px',
          border: `2px solid ${schema.tables_count > 0 ? '#28a745' : '#ffc107'}`
        }}>
          <h3>Schema Discovery Results</h3>
          <p><strong>Database:</strong> {schema.database_info?.name || 'Unknown'}</p>
          <p><strong>Tables Found:</strong> {schema.tables_count}</p>
          <p><strong>Relationships:</strong> {schema.relationships_count}</p>
          
          {schema.tables_count > 0 ? (
            <>
              <p><strong>Detected Tables:</strong> {schema.tables.join(', ')}</p>
              
              {schema.table_purposes.employee_tables.length > 0 && (
                <p><strong>Employee Tables:</strong> {schema.table_purposes.employee_tables.join(', ')}</p>
              )}
              
              {schema.table_purposes.department_tables.length > 0 && (
                <p><strong>Department Tables:</strong> {schema.table_purposes.department_tables.join(', ')}</p>
              )}

              {schema.table_purposes.other_tables.length > 0 && (
                <p><strong>Other Tables:</strong> {schema.table_purposes.other_tables.join(', ')}</p>
              )}
            </>
          ) : (
            <div>
              <p><strong>No tables found in the database.</strong></p>
              <p>This could mean:</p>
              <ul>
                <li>The database is empty</li>
                <li>Tables exist in a different schema</li>
                <li>User doesn't have permission to read tables</li>
              </ul>
              <p>Run the debug script to check what's in the database.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default DatabaseConnector