import React, { useState } from 'react'
import DatabaseConnector from './components/DatabaseConnector'
import DocumentUploader from './components/DocumentUploader'
import QueryPanel from './components/QueryPanel'
import ResultsView from './components/ResultsView'
import MetricsDashboard from './components/MetricsDashboard'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('connect')
  const [connectionString, setConnectionString] = useState('')
  const [schema, setSchema] = useState(null)
  const [queryResults, setQueryResults] = useState(null)
  const [metrics, setMetrics] = useState(null)

  return (
    <div className="app">
      <header className="app-header">
        <h1>NLP Query Engine for Employee Data</h1>
        <nav className="nav-tabs">
          <button 
            className={activeTab === 'connect' ? 'active' : ''}
            onClick={() => setActiveTab('connect')}
          >
            Connect Data
          </button>
          <button 
            className={activeTab === 'query' ? 'active' : ''}
            onClick={() => setActiveTab('query')}
            disabled={!schema}
          >
            Query Data
          </button>
          <button 
            className={activeTab === 'metrics' ? 'active' : ''}
            onClick={() => setActiveTab('metrics')}
          >
            Metrics
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'connect' && (
          <div className="connect-panel">
            <DatabaseConnector 
              onSchemaDiscovered={setSchema}
              connectionString={connectionString}
              onConnectionStringChange={setConnectionString}
            />
            <DocumentUploader />
          </div>
        )}

        {activeTab === 'query' && schema && (
          <div className="query-panel">
            <QueryPanel 
              connectionString={connectionString}
              onResults={setQueryResults}
            />
            <ResultsView results={queryResults} />
          </div>
        )}

        {activeTab === 'metrics' && (
          <MetricsDashboard 
            onMetricsUpdate={setMetrics}
            metrics={metrics}
          />
        )}
      </main>
    </div>
  )
}

export default App