const BASE_URL = 'http://127.0.0.1:8000'

export async function signup({ name, email, password }) {
  const res = await fetch(`${BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Signup failed')
  }
  return res.json() // { token, user_id }
}

export async function login({ email, password }) {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Login failed')
  }
  return res.json() // { token, user_id }
}
export async function fetchTopicGraph() {
  const res = await fetch(`${BASE_URL}/api/quiz/topics/graph`)
  if (!res.ok) throw new Error('Failed to fetch topic graph')
  return res.json() // { topics: [...], prerequisites: [...] }
}

export async function fetchQuizQuestions(topicId) {
  const res = await fetch(`${BASE_URL}/api/quiz?topic=${topicId}`)
  if (!res.ok) throw new Error('Failed to fetch quiz questions')
  return res.json() // { questions: [{ id, question_text, options }] }
}

export async function submitQuizReal(userId, answers, quizType = 'diagnostic') {
  const res = await fetch(`${BASE_URL}/api/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      answers,
      quiz_type: quizType,
    }),
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Submit failed')
  }
  return res.json()
}
export async function fetchMastery(userId) {
  const res = await fetch(`${BASE_URL}/api/assessment/mastery/${userId}`)
  if (!res.ok) throw new Error('Failed to fetch mastery')
  return res.json() // expected: array or object of { topic_id, topic_name, score, level, last_updated }
}
export async function fetchRevisionPlan(userId, simulatedDays = 0) {
  const res = await fetch(
    `${BASE_URL}/api/retention/revision-plan/${userId}?simulated_days=${simulatedDays}`
  )
  if (!res.ok) throw new Error('Failed to fetch revision plan')
  return res.json()
}

export async function fetchResources(topicId, userId) {
  const res = await fetch(
    `${BASE_URL}/api/resources?topic_id=${topicId}&user_id=${userId}`
  )
  if (!res.ok) throw new Error('Failed to fetch resources')
  return res.json()
}