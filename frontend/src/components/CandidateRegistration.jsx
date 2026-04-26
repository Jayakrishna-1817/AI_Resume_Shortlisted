import { useState } from 'react'

export default function CandidateRegistration({ onBack }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  async function handleUpload(e) {
    e.preventDefault()
    if (files.length === 0) return

    setUploading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }

    try {
      // Set a timeout for the fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout for AI parsing

      const res = await fetch('/api/upload-resumes', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      })
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errData.detail || 'Upload failed');
      }
      const data = await res.json()
      setResults(data.results)
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out. AI parsing is taking too long. Please check your API keys and connection.')
      } else {
        setError(err.message)
      }
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button className="btn-secondary" onClick={onBack}>← Back</button>
        <h2 style={{ margin: 0 }}>Candidate Registration</h2>
      </div>

      <p style={{ color: 'var(--text-light)', marginBottom: 24 }}>
        Register new candidates by uploading their resumes (PDF or Text). 
        Our AI will automatically parse their details into the talent pool.
      </p>

      <form onSubmit={handleUpload}>
        <div className="input-group">
          <label>Select Resumes</label>
          <input 
            type="file" 
            multiple 
            accept=".pdf,.txt"
            onChange={(e) => setFiles(Array.from(e.target.files))}
            style={{ padding: '12px', border: '2px dashed var(--border)', borderRadius: 8, cursor: 'pointer' }}
          />
        </div>

        <button 
          type="submit" 
          className="btn-primary" 
          disabled={uploading || files.length === 0}
          style={{ width: '100%', marginTop: 12 }}
        >
          {uploading ? 'Processing... (Trying multiple AI models)' : `Upload & Register ${files.length} Candidates`}
        </button>
      </form>

      {error && <div className="error-message" style={{ marginTop: 16 }}>{error}</div>}

      {results && (
        <div style={{ marginTop: 24 }}>
          <h3>Results</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {results.map((r, i) => (
              <div key={i} className="result-item" style={{ 
                padding: 12, 
                borderRadius: 8, 
                backgroundColor: r.status === 'success' ? '#e6fffa' : '#fff5f5',
                border: `1px solid ${r.status === 'success' ? '#b2f5ea' : '#feb2b2'}`,
                color: '#1a202c' // Dark text for readability
              }}>
                <div style={{ fontWeight: 600 }}>{r.filename}</div>
                <div style={{ fontSize: 13, color: '#4a5568' }}>
                  {r.status === 'success' ? `Successfully parsed ${r.candidate.name}` : r.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
