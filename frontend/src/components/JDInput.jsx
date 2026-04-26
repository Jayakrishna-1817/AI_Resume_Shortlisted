import { useState } from 'react'

const SAMPLE_JDS = {
  "ML Engineer": `Senior Machine Learning Engineer

We are looking for a Senior ML Engineer to join our AI platform team.

Requirements:
- 4+ years of experience in machine learning and model development
- Strong proficiency in Python, PyTorch, and TensorFlow
- Experience with MLOps tools: MLflow, Kubeflow, or similar
- Knowledge of NLP, Transformers, and LLM fine-tuning
- Hands-on experience with model deployment using Docker and Kubernetes
- Familiarity with AWS SageMaker or equivalent cloud ML platforms
- Strong understanding of feature engineering and data pipelines

Preferred:
- Experience with distributed training (CUDA, multi-GPU)
- Contributions to open-source ML projects
- HuggingFace ecosystem experience

Responsibilities:
- Design and build end-to-end ML pipelines
- Deploy and monitor production ML models
- Collaborate with data scientists and product teams
- Drive MLOps best practices across the team

Education: Master's degree in Computer Science, AI, or related field
Experience: 4-8 years
Location: Bangalore / Remote
Type: Full-time`,

  "Backend Engineer": `Backend Software Engineer — Distributed Systems

We are hiring a Senior Backend Engineer to build scalable, high-performance APIs and microservices.

Requirements:
- 3+ years of backend development experience
- Strong skills in Python or Go
- Deep knowledge of REST APIs, gRPC, and Microservices architecture
- Experience with PostgreSQL, Redis, and message queues (Kafka)
- Proficiency with Docker and Kubernetes
- AWS or GCP cloud experience

Preferred:
- Experience with distributed systems patterns (CQRS, event sourcing)
- Familiarity with CI/CD pipelines and DevOps practices
- FastAPI or similar async Python frameworks

Responsibilities:
- Design and implement scalable backend services
- Build APIs consumed by web and mobile clients
- Own service reliability and observability

Education: Bachelor's in Computer Science or equivalent
Experience: 3-7 years
Location: Hyderabad / Remote`,

  "Data Scientist": `Data Scientist — Growth Analytics

Join our data science team to drive key business decisions through data.

Requirements:
- 3+ years of data science experience
- Expert-level Python: Pandas, NumPy, Scikit-learn
- Strong SQL and data querying skills
- Experience with machine learning algorithms and statistical modeling
- Ability to work with Tableau or Power BI for visualization
- Strong communication skills to present findings to non-technical stakeholders

Preferred:
- Experience with NLP or recommendation systems
- Knowledge of A/B testing and experimentation frameworks
- TensorFlow or PyTorch experience

Responsibilities:
- Analyze large datasets to extract actionable insights
- Build predictive models for user behavior
- Design and analyze A/B experiments
- Collaborate with product and engineering teams

Education: Master's in Statistics, Data Science, or related field
Experience: 3-6 years
Location: Mumbai / Remote`,
}

export default function JDInput({ onAnalyze, loading }) {
  const [jdText, setJdText] = useState('')
  const [company, setCompany] = useState('')
  const [topN, setTopN] = useState(8)

  function handleSample(key) {
    setJdText(SAMPLE_JDS[key])
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!jdText.trim()) return
    onAnalyze({ jd_text: jdText, company_name: company || 'TechCorp', top_n: topN })
  }

  return (
    <div className="jd-section">
      <div className="card">
        <div className="card-title">Paste Job Description</div>
        <div className="card-sub">Enter the full JD and let the AI agent handle the rest — parsing, matching, outreach, and ranking.</div>

        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6, display: 'block' }}>
            Try a sample JD:
          </span>
          <div className="sample-jds">
            {Object.keys(SAMPLE_JDS).map(k => (
              <button key={k} className="sample-chip" onClick={() => handleSample(k)}>
                {k}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <textarea
            id="jd-textarea"
            className="jd-textarea"
            placeholder="Paste your Job Description here...&#10;&#10;Include: role, required skills, experience, responsibilities, education."
            value={jdText}
            onChange={e => setJdText(e.target.value)}
            disabled={loading}
          />

          <div className="jd-controls">
            <input
              id="company-input"
              className="company-input"
              placeholder="Company name"
              value={company}
              onChange={e => setCompany(e.target.value)}
              disabled={loading}
            />
            <select
              id="topn-select"
              className="topn-select"
              value={topN}
              onChange={e => setTopN(Number(e.target.value))}
              disabled={loading}
            >
              {[5, 8, 10, 15].map(n => (
                <option key={n} value={n}>Top {n} candidates</option>
              ))}
            </select>
            <button
              id="analyze-btn"
              className="btn-primary"
              type="submit"
              disabled={loading || !jdText.trim()}
            >
              {loading ? 'Analyzing...' : 'Run Agent'}
            </button>
            {jdText && !loading && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setJdText('')}
              >
                Clear
              </button>
            )}
          </div>

          <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
            {jdText.length > 0 && `${jdText.length} characters · `}
            Agent will evaluate {25} candidates in your pool
          </div>
        </form>
      </div>
    </div>
  )
}
