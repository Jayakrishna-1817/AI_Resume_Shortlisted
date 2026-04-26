export default function ParsedJD({ data, mode }) {
  if (!data) return null

  return (
    <div className="parsed-jd">
      <div className="parsed-jd-header">
        <div className="parsed-jd-title">
          Parsed Job Requirements
        </div>
        <span className={`mode-badge ${mode}`}>
          {mode === 'ai' ? 'Gemini AI Mode' : 'Rule-based Mode'}
        </span>
      </div>

      <div className="parsed-grid">
        <div className="parsed-item">
          <label>Role</label>
          <span>{data.role}</span>
        </div>
        <div className="parsed-item">
          <label>Domain</label>
          <span style={{ textTransform: 'replace' }}>{data.domain?.replace(/_/g, ' ')}</span>
        </div>
        <div className="parsed-item">
          <label>Min. Experience</label>
          <span>{data.min_experience}+ years</span>
        </div>
        <div className="parsed-item">
          <label>Education</label>
          <span>{data.education}</span>
        </div>
        <div className="parsed-item">
          <label>Location</label>
          <span>{data.location}</span>
        </div>
        <div className="parsed-item">
          <label>Employment</label>
          <span>{data.employment_type}</span>
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 8 }}>
          Required Skills
        </div>
        <div className="skill-tags">
          {data.required_skills?.map(s => (
            <span key={s} className="skill-tag required">{s}</span>
          ))}
        </div>
      </div>

      {data.preferred_skills?.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 8 }}>
            Preferred Skills
          </div>
          <div className="skill-tags">
            {data.preferred_skills?.map(s => (
              <span key={s} className="skill-tag preferred">{s}</span>
            ))}
          </div>
        </div>
      )}

      {data.key_responsibilities?.length > 0 && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 8 }}>
            Key Responsibilities
          </div>
          <ul style={{ paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {data.key_responsibilities.map((r, i) => (
              <li key={i} style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6 }}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
