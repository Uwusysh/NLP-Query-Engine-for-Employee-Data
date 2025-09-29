import React, { useState, useRef } from 'react'
import axios from 'axios'

const DocumentUploader = () => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState({})
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files)
    handleUpload(files)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    const files = Array.from(event.dataTransfer.files)
    handleUpload(files)
  }

  const handleDragOver = (event) => {
    event.preventDefault()
  }

  const handleUpload = async (files) => {
    if (files.length === 0) return

    setUploading(true)
    setProgress({})
    
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await axios.post('/api/ingest/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setJobId(response.data.job_id)
      checkStatus(response.data.job_id)
      
    } catch (err) {
      console.error('Upload failed:', err)
      setUploading(false)
    }
  }

  const checkStatus = async (jobIdToCheck) => {
    try {
      const response = await axios.get(`/api/ingest/status/${jobIdToCheck}`)
      setStatus(response.data)
      
      if (response.data.status === 'processing') {
        // Check again in 2 seconds
        setTimeout(() => checkStatus(jobIdToCheck), 2000)
      } else {
        setUploading(false)
      }
    } catch (err) {
      console.error('Status check failed:', err)
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2>Document Upload</h2>
      
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        style={{
          border: '2px dashed #007bff',
          borderRadius: '8px',
          padding: '2rem',
          textAlign: 'center',
          marginBottom: '1rem',
          cursor: 'pointer',
          background: uploading ? '#f8f9fa' : 'white'
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          accept=".pdf,.docx,.txt,.csv"
        />
        
        {uploading ? (
          <div>
            <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
            <p>Processing documents...</p>
          </div>
        ) : (
          <div>
            <p>📁 Drag & drop files here or click to browse</p>
            <p style={{ fontSize: '0.9rem', color: '#6c757d', marginTop: '0.5rem' }}>
              Supported formats: PDF, DOCX, TXT, CSV (Max 10MB per file)
            </p>
          </div>
        )}
      </div>

      {status && (
        <div style={{ marginTop: '1rem' }}>
          <h4>Processing Status</h4>
          <p><strong>Status:</strong> {status.status}</p>
          {status.total_files && (
            <>
              <p><strong>Total Files:</strong> {status.total_files}</p>
              <p><strong>Processed:</strong> {status.processed_files}</p>
              <p><strong>Failed:</strong> {status.failed_files}</p>
            </>
          )}
          
          {status.documents && status.documents.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <h5>Document Details:</h5>
              {status.documents.map((doc, index) => (
                <div key={index} style={{ 
                  padding: '0.5rem', 
                  margin: '0.25rem 0', 
                  background: doc.status === 'completed' ? '#d4edda' : '#f8d7da',
                  borderRadius: '4px'
                }}>
                  {doc.filename} - {doc.status}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default DocumentUploader