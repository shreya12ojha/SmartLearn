import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchRoadmap, fetchPacingEstimate } from '../api/mockApi'

const subjectLabels = {
  dsa: 'Data Structures & Algorithms',
  cn: 'Computer Networks',
  os: 'Operating Systems',
  oops: 'OOPs',
  dbms: 'DBMS',
}

// DSA uses the real backend, the other subjects use mock data
const REAL_SUBJECTS = ['dsa']
const REAL_PASS = 0.6   // same pass mark as RealDsaQuiz
const MOCK_PASS = 0.7
const HOURS_PER_TOPIC = 2

function getTier(mastery, passMark = MOCK_PASS) {
  if (mastery === 0) return 'locked'
  if (mastery >= passMark) return 'high'
  if (mastery >= 0.4) return 'mid'
  return 'low'
}

// Turns real topics + real scores into the same shape the mock topics have
function buildRealTopics(realTopics, realMastery) {
  return realTopics.map((t) => ({
    id: t.id,
    name: t.name,
    subject: 'dsa',
    mastery: realMastery[t.id] || 0,
    resource: 'Recommendations coming soon',
  }))
}

// Simple pacing estimate for real topics
function buildRealPacing(topics, hours) {
  const total = topics.length
  const completed = topics.filter((t) => t.mastery >= REAL_PASS).length
  const remaining = total - completed
  return {
    totalSubtopics: total,
    completedSubtopics: completed,
    remaining,
    estimatedDays: Math.ceil((remaining * HOURS_PER_TOPIC) / Math.max(hours || 1, 1)),
  }
}

function Dashboard({ mastery, realMastery = {}, realTopics = [], profile, auth, setAuth, setProfile }) {
  const [topics, setTopics] = useState([])
  const [pacing, setPacing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)
  const navigate = useNavigate()

  const subjects = profile ? [profile.subject] : []
  const [activeSubject, setActiveSubject] = useState(profile?.subject || 'dsa')

  const isReal = REAL_SUBJECTS.includes(activeSubject)
  const passMark = isReal ? REAL_PASS : MOCK_PASS

  // DSA reads real data, other subjects read mock data
  useEffect(() => {
    if (isReal) {
      const list = buildRealTopics(realTopics, realMastery)
      setTopics(list)
      setPacing(list.length > 0 && profile ? buildRealPacing(list, profile.hours) : null)
      setLoading(false)
      return
    }
    setLoading(true)
    Promise.all([
      fetchRoadmap(mastery),
      profile ? fetchPacingEstimate(activeSubject, mastery, profile.hours) : Promise.resolve(null),
    ]).then(([roadmapData, pacingData]) => {
      setTopics(roadmapData.topics.filter((t) => t.subject === activeSubject))
      setPacing(pacingData)
      setLoading(false)
    })
  }, [mastery, realMastery, realTopics, activeSubject, profile, isReal])

  // Close the profile dropdown when clicking anywhere outside it
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    setAuth(null)
    setProfile(null)
    navigate('/')
  }

  const initials = (auth?.name || auth?.email || 'S').charAt(0).toUpperCase()

  const currentTopic = topics.find((t) => t.mastery > 0 && t.mastery < passMark)
  const nextTopic = topics.find((t) => t.mastery === 0)
  const revisionTopics = topics.filter((t) => t.mastery > 0 && t.mastery < 0.4)

  return (
    <div className="dashboard-layout">
      <aside className="dashboard-sidebar">
        <h2 className="sidebar-heading">Your Subjects</h2>
        <div className="subject-list">
          {subjects.map((s) => (
            <button
              key={s}
              className={activeSubject === s ? 'subject-item active' : 'subject-item'}
              onClick={() => setActiveSubject(s)}
            >
              {subjectLabels[s] || s}
            </button>
          ))}
        </div>
      </aside>

      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <h1 className="dashboard-title">{subjectLabels[activeSubject] || activeSubject}</h1>
          <div className="profile-menu-wrapper" ref={menuRef}>
            <button className="profile-avatar" onClick={() => setMenuOpen(!menuOpen)}>
              {initials}
            </button>
            {menuOpen && (
              <div className="profile-dropdown">
                <p className="profile-name">{auth?.name || 'Student'}</p>
                <p className="profile-email">{auth?.email}</p>
                <button className="profile-logout" onClick={handleLogout}>Log Out</button>
              </div>
            )}
          </div>
        </header>

        {loading ? (
          <p className="roadmap-hint">Loading your dashboard...</p>
        ) : (
          <>
            {pacing && (
              <div className="pacing-card">
                {pacing.remaining === 0 ? (
                  <p>🎉 You've completed every subtopic in this subject!</p>
                ) : (
                  <>
                    <p className="pacing-main">
                      Estimated <strong>{pacing.estimatedDays} day{pacing.estimatedDays !== 1 ? 's' : ''}</strong> to finish, at {profile.hours} hr{profile.hours > 1 ? 's' : ''}/day
                    </p>
                    <p className="pacing-sub">
                      {pacing.completedSubtopics} of {pacing.totalSubtopics} subtopics completed · {pacing.remaining} remaining
                    </p>
                  </>
                )}
              </div>
            )}

            <div className="dashboard-grid">
              <div className="dashboard-panel">
                <h3>Currently Attempting</h3>
                {currentTopic ? (
                  <>
                    <p className="panel-topic-name">{currentTopic.name}</p>
                    <p className="panel-sub">{Math.round(currentTopic.mastery * 100)}% complete</p>
                    <button className="panel-btn" onClick={() => navigate('/quiz')}>Continue Quiz</button>
                  </>
                ) : (
                  <p className="panel-empty">Nothing in progress right now.</p>
                )}
              </div>

              <div className="dashboard-panel">
                <h3>Needs Revision</h3>
                {revisionTopics.length > 0 ? (
                  revisionTopics.map((t) => (
                    <div key={t.id} className="panel-row">
                      <span>{t.name}</span>
                      <button
                        className="panel-link-btn"
                        onClick={() => navigate('/quiz', { state: { startAt: { topicId: t.id, subject: activeSubject } } })}
                      >
                        Revise
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="panel-empty">Nothing flagged for revision yet.</p>
                )}
              </div>

              <div className="dashboard-panel">
                <h3>Next Up</h3>
                {nextTopic ? (
                  <>
                    <p className="panel-topic-name">{nextTopic.name}</p>
                    <p className="panel-sub">{nextTopic.resource}</p>
                  </>
                ) : (
                  <p className="panel-empty">You're all caught up!</p>
                )}
              </div>

              <div className="dashboard-panel dashboard-panel-wide">
                <h3>Resources</h3>
                <div className="resource-list">
                  {topics.map((t) => (
                    <div key={t.id} className="resource-row">
                      <span className={`status-icon ${getTier(t.mastery, passMark)}`}>
                        {t.mastery >= passMark ? '✓' : t.mastery > 0 ? '◐' : '○'}
                      </span>
                      <span className="resource-name">{t.name}</span>
                      <span className="resource-link">{t.resource}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Dashboard