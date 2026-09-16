import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchRoadmap, fetchPacingEstimate, checkpointRetest } from '../api/mockApi'
import { fetchTopicGraph } from '../api/realApi'

function getTier(mastery) {
  if (mastery === 0) return 'locked'
  if (mastery >= 0.7) return 'high'
  if (mastery >= 0.4) return 'mid'
  return 'low'
}

function getIcon(tier) {
  if (tier === 'high') return '✓'
  if (tier === 'mid') return '◐'
  if (tier === 'low') return '○'
  return '🔒'
}

function Roadmap({ mastery, profile, realMastery }) {
  const [topics, setTopics] = useState([])
  const [pacing, setPacing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [animated, setAnimated] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [retestingId, setRetestingId] = useState(null)
  const navigate = useNavigate()

  const isDsa = profile?.subject === 'dsa'

  useEffect(() => {
    setLoading(true)
    setAnimated(false)

    if (isDsa) {
      // Real branch: build topic cards from the topic graph + realMastery,
      // only showing topics the user has actually attempted (has a real score for).
      fetchTopicGraph().then((data) => {
        const dsaTopics = data.topics.filter((t) => (t.domain || '').toLowerCase() === 'dsa')
        const attempted = dsaTopics
          .filter((t) => realMastery[t.id] !== undefined)
          .map((t) => ({
            id: t.id,
            name: t.name,
            mastery: realMastery[t.id],
            // TODO: replace with Member 3's real resource once
            // GET /api/resources?topic_id= is wired in.
            resource: 'Resource recommendations coming soon for this topic.',
          }))
        setTopics(attempted)
        setPacing(null) // real pacing needs Member 2's Path Planning Agent; not wired yet
        setLoading(false)
        setTimeout(() => setAnimated(true), 100)
      })
      return
    }

    // Mock branch: unchanged.
    const roadmapPromise = fetchRoadmap(mastery)
    const pacingPromise = profile
      ? fetchPacingEstimate(profile.subject, mastery, profile.hours)
      : Promise.resolve(null)

    Promise.all([roadmapPromise, pacingPromise]).then(([roadmapData, pacingData]) => {
      setTopics(roadmapData.topics)
      setPacing(pacingData)
      setLoading(false)
      setTimeout(() => setAnimated(true), 100)
    })
  }, [mastery, profile, realMastery, isDsa])

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const handleRetest = async (e, topicId) => {
    e.stopPropagation()
    if (isDsa) {
      // Real DSA retest: no mock checkpoint call needed — just jump straight
      // into RealDsaQuiz at this topic.
      navigate('/quiz', { state: { startAt: { subject: 'dsa', topicId } } })
      return
    }
    setRetestingId(topicId)
    const checkpoint = await checkpointRetest(topicId)
    setRetestingId(null)
    if (checkpoint) {
      navigate('/quiz', { state: { startAt: checkpoint } })
    }
  }

  if (loading) {
    return (
      <div className="roadmap-container">
        <h1 className="roadmap-title">Your {isDsa ? 'DSA' : ''} Roadmap</h1>
        <p className="roadmap-hint">Loading your progress...</p>
      </div>
    )
  }

  return (
    <div className="roadmap-container">
      <h1 className="roadmap-title">Your Roadmap</h1>

      {isDsa && topics.length === 0 && (
        <p className="roadmap-hint">Take the DSA quiz to see your progress here.</p>
      )}

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

      <div className="mastery-list">
        {topics.map((topic) => {
          const tier = getTier(topic.mastery)
          const isLocked = tier === 'locked'
          const isExpanded = expandedId === topic.id

          return (
            <div
              key={topic.id}
              className={`mastery-card ${isLocked ? 'locked' : ''} ${isExpanded ? 'expanded' : ''}`}
              onClick={() => !isLocked && toggleExpand(topic.id)}
            >
              <div className="mastery-row-top">
                <span className="mastery-topic">
                  <span className={`status-icon ${tier}`}>{getIcon(tier)}</span>
                  {topic.name}
                </span>
                <span className="mastery-percent">{Math.round(topic.mastery * 100)}%</span>
              </div>

              <div className="mastery-track">
                <div
                  className={`mastery-fill ${tier}`}
                  style={{ width: animated ? `${topic.mastery * 100}%` : '0%' }}
                />
              </div>

              {isExpanded && (
                <div className="mastery-detail">
                  <p>📚 {topic.resource}</p>
                  <button
                    className="retest-btn"
                    onClick={(e) => handleRetest(e, topic.id)}
                    disabled={retestingId === topic.id}
                  >
                    {retestingId === topic.id ? 'Loading...' : '🔁 Retest this topic'}
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <p className="roadmap-hint">Tap a topic to see its recommended resource</p>
    </div>
  )
}

export default Roadmap