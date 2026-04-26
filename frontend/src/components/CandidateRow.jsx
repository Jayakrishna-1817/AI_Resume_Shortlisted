import { useState } from 'react'

function ScorePill({ label, value, type }) {
  return (
    <div className={`score-pill ${type}`}>
      <div className="score-label">{label}</div>
      <div className="score-value">{value.toFixed(1)}</div>
      <div className="score-bar-track">
        <div className={`score-bar-fill ${type}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function RankBadge({ rank }) {
  const cls = rank === 1 ? 'r1' : rank === 2 ? 'r2' : rank === 3 ? 'r3' : 'rN'
  const icon = rank === 1 ? '#1' : rank === 2 ? '#2' : rank === 3 ? '#3' : rank
  return <div className={`rank-badge ${cls}`}>{icon}</div>
}

function Conversation({ messages }) {
  return (
    <div className="conversation">
      {messages.map((msg, i) => (
        <div key={i} className={`msg ${msg.role}`}>
          <div className="msg-avatar">
            {msg.role === 'recruiter' ? 'AI' : 'C'}
          </div>
          <div>
            <div className="msg-role-label">
              {msg.role === 'recruiter' ? 'AI Recruiter' : 'Candidate'}
            </div>
            <div className="msg-bubble">{msg.content}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function CandidateRow({ item }) {
  const [expanded, setExpanded] = useState(false)
  const c = item.candidate

  return (
    <div
      className={`candidate-row rank-${item.rank}`}
      onClick={() => setExpanded(e => !e)}
    >
      <div className="cand-top">
        <RankBadge rank={item.rank} />

        <div className="cand-info">
          <div className="cand-name">{c.name}</div>
          <div className="cand-role">{c.current_role} @ {c.current_company}</div>
          <div className="cand-meta">
            <span>{c.location}</span>
            <span>{c.years_experience}yr exp</span>
            <span className={`avail-badge ${c.available ? 'yes' : 'no'}`}>
              {c.available ? 'Available' : 'Not actively looking'}
            </span>
            {c.notice_period && <span>{c.notice_period} notice</span>}
          </div>
        </div>

        <div className="scores-row" onClick={e => e.stopPropagation()}>
          <ScorePill label="Match" value={item.match_score} type="match" />
          <ScorePill label="Interest" value={item.interest_score} type="interest" />
          <ScorePill label="Combined" value={item.combined_score} type="combined" />
        </div>
      </div>

      {/* Quick skills preview */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
        {item.matched_skills.slice(0, 6).map(s => (
          <span key={s} style={{ padding: '2px 8px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 100, fontSize: 11, color: '#34d399' }}>
            ✓ {s}
          </span>
        ))}
        {item.missing_skills.slice(0, 3).map(s => (
          <span key={s} style={{ padding: '2px 8px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.18)', borderRadius: 100, fontSize: 11, color: '#f87171' }}>
            ✗ {s}
          </span>
        ))}
      </div>

      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
        {expanded ? '▲ Click to collapse' : '▼ Click to expand — conversation & full analysis'}
      </div>

      {expanded && (
        <div className="cand-detail" onClick={e => e.stopPropagation()}>
          {/* Sub-scores */}
          <div className="sub-scores">
            <div className="sub-score-card">
              <div className="label">Skills</div>
              <div className="val" style={{ color: 'var(--accent)' }}>{item.skill_score.toFixed(0)}</div>
            </div>
            <div className="sub-score-card">
              <div className="label">Experience</div>
              <div className="val" style={{ color: 'var(--teal)' }}>{item.experience_score.toFixed(0)}</div>
            </div>
            <div className="sub-score-card">
              <div className="label">Domain</div>
              <div className="val" style={{ color: 'var(--green)' }}>{item.domain_score.toFixed(0)}</div>
            </div>
            <div className="sub-score-card">
              <div className="label">Education</div>
              <div className="val" style={{ color: 'var(--yellow)' }}>{item.education_score.toFixed(0)}</div>
            </div>
          </div>

          <div className="detail-grid">
            <div className="detail-section">
              <h4>Match Analysis</h4>
              <div className="explanation-text">{item.match_explanation}</div>
            </div>
            <div className="detail-section">
              <h4>Interest Signals</h4>
              <div className="signal-list">
                <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 8, fontStyle: 'italic' }}>
                  {item.interest_summary}
                </div>
                {item.key_signals.map((s, i) => (
                  <div key={i} className="signal-item">{s}</div>
                ))}
              </div>
            </div>
          </div>

          <div>
            <h4 style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 12 }}>
              Simulated Outreach Conversation
            </h4>
            <Conversation messages={item.conversation} />
          </div>

          <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap', fontSize: 13, color: 'var(--text-muted)' }}>
            <span>Email: {c.email}</span>
            <span>Phone: {c.phone}</span>
            {c.salary_expectation && <span>Salary: {c.salary_expectation}</span>}
          </div>
        </div>
      )}
    </div>
  )
}
