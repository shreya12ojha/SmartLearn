import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { fetchTopicGraph, fetchQuizQuestions, submitQuizReal, fetchResources } from '../api/realApi'
import { topoSortTopics } from '../utils/topoSort'

const PASS_THRESHOLD = 0.6

function RealDsaQuiz({ mastery = {}, setMastery, auth }) {
  const [orderedTopics, setOrderedTopics] = useState([])
  const [topicIndex, setTopicIndex] = useState(0)
  const [questions, setQuestions] = useState([])       // full question set for this topic
  const [activeQuestions, setActiveQuestions] = useState([]) // subset currently being tested
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [results, setResults] = useState([])
  const [lastScore, setLastScore] = useState(0)
  const [phase, setPhase] = useState('loading') // loading | testing | reviewing | fail | complete | error
  const [errorMsg, setErrorMsg] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [resources, setResources] = useState([])
  const [resourcesLoading, setResourcesLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const startAt = location.state?.startAt
  const isRetestMode = !!startAt?.topicId

  useEffect(() => {
    if (!auth?.userId) {
      setPhase('error')
      setErrorMsg('You need to be logged in to take this quiz.')
      return
    }

    setPhase('loading')
    fetchTopicGraph()
      .then((data) => {
        const dsaTopics = data.topics.filter((t) => (t.domain || '').toLowerCase() === 'dsa')
        if (dsaTopics.length === 0) {
          setPhase('error')
          setErrorMsg('No DSA topics found in the database yet.')
          return
        }
        const ordered = topoSortTopics(dsaTopics, data.prerequisites)
        setOrderedTopics(ordered)
        const startIndex = isRetestMode
          ? Math.max(ordered.findIndex((t) => t.id === startAt.topicId), 0)
          : 0
        setTopicIndex(startIndex)
      })
      .catch(() => {
        setPhase('error')
        setErrorMsg('Could not load the topic list. Is the backend running?')
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.key])

  useEffect(() => {
    if (orderedTopics.length === 0) return
    const topic = orderedTopics[topicIndex]
    if (!topic) return

    setPhase('loading')
    setCurrentIndex(0)
    setAnswers({})
    fetchQuizQuestions(topic.id)
      .then((data) => {
        setQuestions(data.questions)
        setActiveQuestions(data.questions) // start with the full set
        setPhase('testing')
      })
      .catch(() => {
        setPhase('error')
        setErrorMsg(`Could not load questions for ${topic.name}.`)
      })
  }, [topicIndex, orderedTopics])

  const currentTopic = orderedTopics[topicIndex]

  // Fetch real recommended resources when a topic is failed
  useEffect(() => {
    if (phase !== 'fail' || !currentTopic || !auth?.userId) return
    setResourcesLoading(true)
    fetchResources(currentTopic.id, auth.userId)
      .then((data) => setResources(data.recommended_resources || []))
      .catch(() => setResources([]))
      .finally(() => setResourcesLoading(false))
  }, [phase, currentTopic, auth])

  if (phase === 'loading') {
    return (
      <div className="quiz-container">
        <p className="quiz-meta">Loading your DSA quiz...</p>
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="quiz-container">
        <h1>Something went wrong</h1>
        <p className="quiz-meta">{errorMsg}</p>
      </div>
    )
  }

  if (phase === 'complete') {
    return (
      <div className="quiz-container">
        <h1>All DSA Topics Complete</h1>
        <p className="quiz-meta">
          You've worked through every real DSA topic. Check your Roadmap for the full picture.
        </p>
      </div>
    )
  }

  const getQuestionById = (id) => questions.find((q) => q.id === id)
  const currentQuestion = activeQuestions[currentIndex]
  const allAnswered = activeQuestions.every((q) => answers[q.id] !== undefined)
  const progressPercent =
    ((topicIndex + (currentIndex + 1) / activeQuestions.length) / orderedTopics.length) * 100

  const handleSelect = (optionKey) => {
    setAnswers({ ...answers, [currentQuestion.id]: optionKey })
  }

  const goBack = () => setCurrentIndex((i) => Math.max(i - 1, 0))
  const goNext = () => setCurrentIndex((i) => Math.min(i + 1, activeQuestions.length - 1))

  const submitAndEvaluate = async () => {
    setSubmitting(true)
    try {
      const answersArray = activeQuestions.map((q) => ({
        question_id: q.id,
        selected_option: answers[q.id],
      }))
      const quizType = isRetestMode ? 'checkpoint' : 'diagnostic'
      const response = await submitQuizReal(auth.userId, answersArray, quizType)
      const score = response.mastery[String(currentTopic.id)] ?? response.mastery[currentTopic.id] ?? 0

      setMastery({ ...mastery, [currentTopic.id]: Math.max(mastery[currentTopic.id] || 0, score) })
      setResults(response.results || [])
      setLastScore(score)
      setPhase('reviewing')
    } catch (err) {
      setPhase('error')
      setErrorMsg(err.message || 'Failed to submit your answers.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleContinueFromReview = () => {
    if (lastScore >= PASS_THRESHOLD) {
      if (isRetestMode) {
        navigate('/dashboard')
        return
      }
      if (topicIndex < orderedTopics.length - 1) {
        setTopicIndex(topicIndex + 1)
      } else {
        setPhase('complete')
      }
    } else {
      // Retry-smarter: narrow to only the missed questions from the full set.
      const missedIds = results.filter((r) => !r.is_correct).map((r) => r.question_id)
      const missedQuestions = questions.filter((q) => missedIds.includes(q.id))
      setActiveQuestions(missedQuestions.length > 0 ? missedQuestions : questions)
      setPhase('fail')
    }
  }

  const handleRetry = () => {
    setCurrentIndex(0)
    setAnswers({})
    setPhase('testing')
  }

  if (phase === 'reviewing') {
    const correctCount = results.filter((r) => r.is_correct).length
    return (
      <div className="quiz-container">
        <h1>Review: {currentTopic.name}</h1>
        <p className="quiz-meta">
          {correctCount} of {results.length} correct — {Math.round(lastScore * 100)}% on this attempt
        </p>

        <div className="review-list">
          {results.map((r) => {
            const q = getQuestionById(r.question_id)
            return (
              <div key={r.question_id} className={`review-item ${r.is_correct ? 'correct' : 'incorrect'}`}>
                <p className="review-question">
                  {r.is_correct ? '✅' : '❌'} {r.question_text}
                </p>
                <p className="review-answer">
                  Your answer: <strong>{q?.options?.[r.selected_option] || r.selected_option}</strong>
                </p>
                {!r.is_correct && (
                  <p className="review-answer correct-answer">
                    Correct answer: <strong>{q?.options?.[r.correct_option] || r.correct_option}</strong>
                  </p>
                )}
              </div>
            )
          })}
        </div>

        <button className="quiz-next-btn enabled" onClick={handleContinueFromReview}>
          Continue
        </button>
      </div>
    )
  }

  if (phase === 'fail') {
    return (
      <div className="quiz-container">
        <h1>Let's revisit {currentTopic.name}</h1>
        <p className="quiz-meta">
          You'll be retested on just the {activeQuestions.length} question{activeQuestions.length !== 1 ? 's' : ''} you missed — review these first, then retake.
        </p>

        {resourcesLoading ? (
          <p className="quiz-meta">Loading recommended resources...</p>
        ) : resources.length > 0 ? (
          <div className="resource-list-quiz">
            {resources.map((r) => (
              <a key={r.id} href={r.url} target="_blank" rel="noreferrer" className="resource-card-link">
                <span className="resource-format-tag">{r.format}</span>
                <span className="resource-card-title">{r.title}</span>
                <span className="resource-card-meta">{r.platform} · ~{r.estimated_minutes} min</span>
              </a>
            ))}
          </div>
        ) : (
          <div className="resource-card">📚 No specific resources found yet — review your notes on this topic and retry.</div>
        )}

        <button className="quiz-next-btn enabled" onClick={handleRetry}>
          I've reviewed it — Retry Quiz
        </button>
      </div>
    )
  }

  return (
    <div className="quiz-container">
      <h1>DSA</h1>
      <p className="quiz-meta">
        {isRetestMode && <span className="retest-badge">🔁 Retest</span>}
        {currentTopic.name} · Question {currentIndex + 1} of {activeQuestions.length}
        {!isRetestMode && ` · Topic ${topicIndex + 1} of ${orderedTopics.length}`}
      </p>

      <div className="quiz-progress-track">
        <div className="quiz-progress-fill" style={{ width: `${progressPercent}%` }} />
      </div>

      <div className="question-navigator">
        {activeQuestions.map((q, i) => {
          const answered = answers[q.id] !== undefined
          const isCurrent = i === currentIndex
          return (
            <button
              key={q.id}
              className={`nav-dot ${answered ? 'answered' : ''} ${isCurrent ? 'current' : ''}`}
              onClick={() => setCurrentIndex(i)}
            >
              {i + 1}
            </button>
          )
        })}
      </div>

      <p className="quiz-question">{currentQuestion.question_text}</p>

      <div className="quiz-options">
        {Object.entries(currentQuestion.options).map(([key, text]) => (
          <button
            key={key}
            className={answers[currentQuestion.id] === key ? 'quiz-option selected' : 'quiz-option'}
            onClick={() => handleSelect(key)}
          >
            {text}
          </button>
        ))}
      </div>

      <div className="quiz-nav-row">
        <button className="quiz-back-btn" onClick={goBack} disabled={currentIndex === 0}>
          ← Back
        </button>
        {currentIndex < activeQuestions.length - 1 ? (
          <button className="quiz-next-btn enabled" onClick={goNext}>
            Next →
          </button>
        ) : (
          <button
            className={allAnswered ? 'quiz-next-btn enabled' : 'quiz-next-btn'}
            disabled={!allAnswered || submitting}
            onClick={submitAndEvaluate}
          >
            {submitting ? 'Submitting...' : 'Submit Quiz'}
          </button>
        )}
      </div>
    </div>
  )
}

export default RealDsaQuiz