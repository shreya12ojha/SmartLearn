import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchRoadmap, fetchPacingEstimate } from '../api/mockApi'
import { fetchRevisionPlan, fetchResources } from '../api/realApi'

const subjectLabels = {
  dsa: 'Data Structures & Algorithms',
  cn: 'Computer Networks',
  os: 'Operating Systems',
  oops: 'OOPs',
  dbms: 'DBMS',
}

const REAL_SUBJECTS = ['dsa']
const REAL_PASS = 0.6
const MOCK_PASS = 0.7
const HOURS_PER_TOPIC = 2

function getTier(mastery, passMark = MOCK_PASS) {
  if (mastery === 0) return 'locked'
  if (mastery >= passMark) return 'high'
  if (mastery >= 0.4) return 'mid'
  return 'low'
}

function buildRealTopics(realTopics, realMastery) {
  return realTopics.map((t) => ({
    id: t.id,
    name: t.name,
    subject: 'dsa',
    mastery: realMastery[t.id] || 0,
    resource: 'Recommendations coming soon',
  }))
}

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
  const [revisionPlan, setRevisionPlan] = useState([])
  const [expandedTopicId, setExpandedTopicId] = useState(null)
  const [resourceCache, setResourceCache] = useState({})
  const menuRef = useRef(null)
  const navigate = useNavigate()

  const subjects = profile ? [profile.subject] : []
  const [activeSubject, setActiveSubject] = useState(profile?.subject || 'dsa')

  const isReal = REAL_SUBJECTS.includes(activeSubject)
  const passMark = isReal ? REAL_PASS : MOCK_PASS

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

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (!isReal || !auth?.userId) {
      setRevisionPlan([])
      return
    }
    fetchRevisionPlan(auth.userId)
      .then((data) => setRevisionPlan(data.revision_topics || []))
      .catch(() => setRevisionPlan([]))
  }, [isReal, auth, realMastery])

  const handleLogout = () => {
    setAuth(null)
    setProfile(null)
    navigate('/')
  }

  const handleToggleResources = (topicId) => {
    if (expandedTopicId === topicId) {
      setExpandedTopicId(null)
      return
    }
    setExpandedTopicId(topicId)
    if (!resourceCache[topicId] && isReal && auth?.userId) {
      fetchResources(topicId, auth.userId)
        .then((data) => setResourceCache((prev) => ({ ...prev, [topicId]: data.recommended_resources || [] })))
        .catch(() => setResourceCache((prev) => ({ ...prev, [topicId]: [] })))
    }
  }

  const initials = (auth?.name || auth?.email || 'S').charAt(0).toUpperCase()

  const currentTopic = topics.find((t) => t.mastery > 0 && t.mastery < passMark)
  const nextTopic = topics.find((t) => t.mastery === 0)
  const revisionTopics = isReal
    ? revisionPlan.filter((r) => r.needs_revision)
    : topics.filter((t) => t.mastery > 0 && t.mastery < 0.4)

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
                  revisionTopics.map((t) => {
                    const id = isReal ? t.topic_id : t.id
                    const name = isReal ? t.topic_name : t.name
                    return (
                      <div key={id} className="panel-row">
                        <span>
                          {name}
                          {isReal && <span className="decay-tag"> · {Math.round(t.decayed_mastery * 100)}%</span>}
                        </span>
                        <button
                          className="panel-link-btn"
                          onClick={() => navigate('/quiz', { state: { startAt: { topicId: id, subject: activeSubject } } })}
                        >
                          Revise
                        </button>
                      </div>
                    )
                  })
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
                    <div key={t.id}>
                      <div className="resource-row resource-row-clickable" onClick={() => handleToggleResources(t.id)}>
                        <span className={`status-icon ${getTier(t.mastery, passMark)}`}>
                          {t.mastery >= passMark ? '✓' : t.mastery > 0 ? '◐' : '○'}
                        </span>
                        <span className="resource-name">{t.name}</span>
                        <span className="resource-link">{expandedTopicId === t.id ? 'Hide' : 'View resources'}</span>
                      </div>
                      {expandedTopicId === t.id && (
                        <div className="resource-expand">
                          {!resourceCache[t.id] ? (
                            <p className="panel-empty">Loading...</p>
                          ) : resourceCache[t.id].length === 0 ? (
                            <p className="panel-empty">No resources found for this topic yet.</p>
                          ) : (
                            resourceCache[t.id].map((r) => (
                              <a key={r.id} href={r.url} target="_blank" rel="noreferrer" className="resource-card-link">
                                <span className="resource-format-tag">{r.format}</span>
                                <span className="resource-card-title">{r.title}</span>
                                <span className="resource-card-meta">{r.platform} · ~{r.estimated_minutes} min</span>
                              </a>
                            ))
                          )}
                        </div>
                      )}
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