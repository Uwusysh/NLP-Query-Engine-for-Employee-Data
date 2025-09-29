import React, { useState, useEffect } from 'react'
import axios from 'axios'

const MetricsDashboard = ({ onMetricsUpdate, metrics }) => {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      const response = await axios.get('/api/query/metrics')
      onMetricsUpdate(response.data)
    } catch (err) {
      console.error('Failed to load metrics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="card">
        <h2>Performance Metrics</h2>
        <div className="spinner" style={{ margin: '2rem auto' }}></div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="card">
        <h2>Performance Metrics</h2>
        <p>No metrics available</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>Performance Metrics</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <MetricCard 
          title="Average Response Time" 
          value={`${metrics.avg_response_time}s`}
          color="#007bff"
        />
        <MetricCard 
          title="Cache Hit Rate" 
          value={`${metrics.cache_hit_rate}%`}
          color="#28a745"
        />
        <MetricCard 
          title="Total Queries" 
          value={metrics.total_queries}
          color="#6c757d"
        />
        <MetricCard 
          title="Active Connections" 
          value={metrics.active_connections}
          color="#fd7e14"
        />
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        <div className="card">
          <h3>Query Performance</h3>
          <p>Recent queries (last hour): {metrics.recent_queries}</p>
          {/* In a real app, you'd have charts here */}
          <div style={{ 
            height: '100px', 
            background: 'linear-gradient(90deg, #007bff 0%, #28a745 100%)',
            borderRadius: '4px',
            opacity: 0.7
          }}></div>
        </div>

        <div className="card">
          <h3>System Health</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <HealthIndicator title="Database" status="healthy" />
            <HealthIndicator title="Document Processing" status="healthy" />
            <HealthIndicator title="Query Engine" status="healthy" />
            <HealthIndicator title="Cache" status="healthy" />
          </div>
        </div>
      </div>
    </div>
  )
}

const MetricCard = ({ title, value, color }) => (
  <div className="card" style={{ textAlign: 'center', borderTop: `4px solid ${color}` }}>
    <h3 style={{ color, fontSize: '2rem', margin: '0.5rem 0' }}>{value}</h3>
    <p style={{ color: '#6c757d', margin: 0 }}>{title}</p>
  </div>
)

const HealthIndicator = ({ title, status }) => (
  <div style={{ textAlign: 'center' }}>
    <div 
      style={{
        width: '12px',
        height: '12px',
        borderRadius: '50%',
        background: status === 'healthy' ? '#28a745' : '#dc3545',
        margin: '0 auto 0.5rem'
      }}
    ></div>
    <div style={{ fontSize: '0.9rem' }}>{title}</div>
    <div style={{ fontSize: '0.8rem', color: '#6c757d' }}>{status}</div>
  </div>
)

export default MetricsDashboard