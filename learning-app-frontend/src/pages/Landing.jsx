import { useNavigate } from 'react-router-dom'

function Landing() {
  const navigate = useNavigate()

  return (
    <div className="landing-page">
      <header className="landing-header">
        <span className="landing-logo">SmartLearn</span>
        <button className="landing-header-login" onClick={() => navigate('/login')}>
          Log In
        </button>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-text">
          <h1 className="landing-headline">Skip what you know.<br />Master what you don't.</h1>
          <p className="landing-subtext">Adaptive prep for DSA, CN, OS, OOPs & DBMS.</p>
          <div className="landing-actions">
            <button className="landing-btn primary" onClick={() => navigate('/signup')}>
              Get Started
            </button>
            <button className="landing-btn secondary" onClick={() => navigate('/login')}>
              Log In
            </button>
          </div>
        </div>

        <div className="landing-hero-graphic">
          <svg viewBox="0 0 320 320" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M40 260 C 90 260, 90 180, 140 180 S 190 100, 240 100 S 280 60, 280 60"
                  stroke="#6366f1" strokeWidth="3" strokeDasharray="6 8" strokeLinecap="round"/>
            <circle cx="40" cy="260" r="14" fill="#22c55e"/>
            <circle cx="140" cy="180" r="14" fill="#22c55e"/>
            <circle cx="240" cy="100" r="14" fill="#eab308"/>
            <circle cx="280" cy="60" r="14" fill="#334155" stroke="#64748b" strokeWidth="2"/>
          </svg>
        </div>
      </section>

      <section className="landing-features">
        <div className="feature-card">
          <div className="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M12 20v-6M12 14l6-3.5V4L12 7.5 6 4v6.5L12 14z" strokeLinejoin="round"/>
            </svg>
          </div>
          <h3>Adaptive Quizzes</h3>
          <p>Questions that adjust to your level, topic by topic.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M4 19V10M11 19V4M18 19v-7" strokeLinecap="round"/>
            </svg>
          </div>
          <h3>Live Mastery Tracking</h3>
          <p>Watch your progress update as you learn, in real time.</p>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M9 20l-5-2V6l5 2m0 12l6-2m-6 2V8m6 10l5-2V4l-5 2m0 12V10m0-2L9 6" strokeLinejoin="round"/>
            </svg>
          </div>
          <h3>Personalized Roadmap</h3>
          <p>A clear path through every topic you need for placements.</p>
        </div>
      </section>
    </div>
  )
}

export default Landing