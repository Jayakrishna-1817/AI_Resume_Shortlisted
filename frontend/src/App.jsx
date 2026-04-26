import { useState } from 'react'
import JDInput from './components/JDInput.jsx'
import ParsedJD from './components/ParsedJD.jsx'
import CandidateRow from './components/CandidateRow.jsx'
import CandidateRegistration from './components/CandidateRegistration.jsx'

const LOADING_STEPS = [
  { id: 1, label: 'Parsing job description with AI' },
  { id: 2, label: 'Discovering matching candidates' },
  { id: 3, label: 'Computing match & skill scores' },
  { id: 4, label: 'Simulating conversational outreach' },
  { id: 5, label: 'Ranking shortlist by combined score' },
]

function LoadingView({ step }) {
  return (
    <div className="loading-wrapper">
      <div className="loading-spinner" />
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)' }}>Agent is working...</div>
      <div className="loading-steps">
        {LOADING_STEPS.map((s, i) => {
          const status = i + 1 < step ? 'done' : i + 1 === step ? 'active' : ''
          return (
            <div key={s.id} className={`loading-step ${status}`}>
              <div className="loading-dot" />
              <span>{s.label}</span>
              {status === 'done' && <span style={{ marginLeft: 'auto', fontSize: 12 }}>✓</span>}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function StepsBar({ step }) {
  const steps = ['Input JD', 'Parse', 'Match', 'Engage', 'Shortlist']
  return (
    <div className="steps-bar">
      {steps.map((s, i) => {
        const num = i + 1
        const status = num < step ? 'done' : num === step ? 'active' : ''
        return (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div className={`step-item ${status}`}>
              <div className="step-num">{status === 'done' ? '✓' : num}</div>
              {s}
            </div>
            {i < steps.length - 1 && <span className="step-arrow">›</span>}
          </div>
        )
      })}
    </div>
  )
}

function exportCSV(shortlist, parsedJd) {
  const headers = ['Rank', 'Name', 'Role', 'Company', 'Experience (yr)', 'Location', 'Available', 'Match Score', 'Interest Score', 'Combined Score', 'Matched Skills', 'Missing Skills', 'Interest Summary']
  const rows = shortlist.map(item => {
    const c = item.candidate
    return [
      item.rank, c.name, c.current_role, c.current_company, c.years_experience,
      c.location, c.available ? 'Yes' : 'No',
      item.match_score, item.interest_score, item.combined_score,
      item.matched_skills.join('; '), item.missing_skills.join('; '),
      item.interest_summary
    ]
  })
  const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `talent-shortlist-${parsedJd?.role?.replace(/\s+/g, '-') || 'results'}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function App() {
  const [view, setView] = useState('analyzer') // 'analyzer' or 'registration'
  const [loading, setLoading] = useState(false)
  const [loadStep, setLoadStep] = useState(1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [uiStep, setUiStep] = useState(1)

  async function handleAnalyze(params) {
    setLoading(true)
    setError(null)
    setResult(null)
    setUiStep(2)

    // Animate loading steps
    for (let i = 1; i <= 5; i++) {
      setLoadStep(i)
      await new Promise(r => setTimeout(r, 150))
    }

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      })
      if (!res.ok) {
        const text = await res.text()
        let detail = 'Server error'
        try {
          const err = JSON.parse(text)
          detail = err.detail || detail
        } catch (e) {
          detail = text.slice(0, 100) || detail
        }
        throw new Error(detail)
      }
      const data = await res.json()
      setResult(data)
      setUiStep(5)
    } catch (e) {
      setError(e.message)
      setUiStep(1)
    } finally {
      setLoading(false)
    }
  }

  const avgMatch = result ? (result.shortlist.reduce((s, x) => s + x.match_score, 0) / result.shortlist.length).toFixed(1) : null
  const avgInterest = result ? (result.shortlist.reduce((s, x) => s + x.interest_score, 0) / result.shortlist.length).toFixed(1) : null
  const availableCount = result ? result.shortlist.filter(x => x.candidate.available).length : null

  return (
    <div className="app">
      {/* Hero */}
      <div className="hero">
        
        <h1>AI Talent Scouting Agent</h1>
        <p>
          Drop a Job Description. The agent parses it, discovers matching candidates,
          simulates real conversations, and hands you a ranked shortlist — instantly.
        </p>
        
        {view === 'analyzer' && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 12, marginBottom: 32 }}>
            <button className="btn-secondary" onClick={() => setView('registration')}>
              Register Candidates (Resume Upload)
            </button>
          </div>
        )}

        <StepsBar step={uiStep} />
      </div>

      {/* Main */}
      <div className="main-content">
        {error && (
          <div className="error-box">
            Error: {error}
          </div>
        )}

        {view === 'registration' ? (
          <CandidateRegistration onBack={() => setView('analyzer')} />
        ) : (
          <>
            {/* JD Input always visible unless loading */}
            {!loading && (
              <JDInput onAnalyze={handleAnalyze} loading={loading} />
            )}

            {/* Loading */}
            {loading && <LoadingView step={loadStep} />}

            {/* Results */}
            {result && !loading && (
              <>
                <ParsedJD data={result.parsed_jd} />

                {/* Stats row */}
                <div className="stats-row">
                  <div className="stat-card">
                    <div className="stat-val">{result.total_candidates_evaluated}</div>
                    <div className="stat-label">Candidates Evaluated</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-val">{result.shortlist.length}</div>
                    <div className="stat-label">Shortlisted</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-val" style={{ color: 'var(--accent)' }}>{avgMatch}</div>
                    <div className="stat-label">Avg. Match Score</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-val" style={{ color: 'var(--teal)' }}>{avgInterest}</div>
                    <div className="stat-label">Avg. Interest Score</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-val" style={{ color: 'var(--green)' }}>{availableCount}</div>
                    <div className="stat-label">Currently Available</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-val" style={{ color: 'var(--yellow)', fontSize: 16 }}>{result.processing_time_seconds}s</div>
                    <div className="stat-label">Processing Time</div>
                  </div>
                </div>

                {/* Export + Results */}
                <div className="export-bar">
                  <span>
                    Ranked shortlist for <strong>{result.parsed_jd.role}</strong> — sorted by Combined Score (60% Match + 40% Interest)
                  </span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      className="btn-secondary"
                      onClick={() => exportCSV(result.shortlist, result.parsed_jd)}
                    >
                      Export CSV
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => { setResult(null); setUiStep(1); }}
                    >
                      New Search
                    </button>
                  </div>
                </div>

                <div className="shortlist-grid">
                  {result.shortlist.map(item => (
                    <CandidateRow key={item.candidate.id} item={item} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>

      <div className="footer">
        Built for Catalyst Hackathon by Deccan AI · AI Talent Scouting Agent ·
        Scores: Match (skill + exp + domain + edu) + Interest (availability + sentiment + engagement)
      </div>
    </div>
  )
}
