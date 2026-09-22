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

export async function fetchQuizQuestions(topicId, userId) {
  const res = await fetch(`${BASE_URL}/api/quiz?topic=${topicId}&user_id=${userId}`)
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
  return res.json() // { user_id, mastery: [{ topic_id, topic_name, mastery_score, mastery_level, last_updated }] }
}

export async function fetchRevisionPlan(userId, simulatedDays = 0) {
  const res = await fetch(`${BASE_URL}/api/retention/revision-plan/${userId}?simulated_days=${simulatedDays}`)
  if (!res.ok) throw new Error('Failed to fetch revision plan')
  return res.json() // { user_id, simulated_days, revision_topics: [...] }
}

export async function fetchResources(topicId, userId) {
  const res = await fetch(`${BASE_URL}/api/resources?topic_id=${topicId}&user_id=${userId}`)
  if (!res.ok) throw new Error('Failed to fetch resources')
  return res.json() // { topic_id, topic_name, recommended_resources: [...] }
}

export async function fetchPathPlanningRoadmap(userId) {
  const res = await fetch(`${BASE_URL}/api/path-planning/roadmap/${userId}`)
  if (!res.ok) throw new Error('Failed to fetch roadmap')
  return res.json()
  // { user_id, weekly_budget, allocated_minutes, remaining_budget,
  //   next_topic, roadmap: [...], summary: {...} }
}

export async function fetchNextTopic(userId) {
  const res = await fetch(`${BASE_URL}/api/path-planning/next-topic/${userId}`)
  if (!res.ok) throw new Error('Failed to fetch next topic')
  return res.json() // { user_id, next_topic, reason }
}

export async function fetchResourceRecommendation(userId, topicId) {
  const res = await fetch(
    `${BASE_URL}/api/recommendations/resource?user_id=${userId}&topic_id=${topicId}`
  )
  if (!res.ok) throw new Error('Failed to fetch resource recommendation')
  return res.json()
  // { topic_id, topic_name, selected_arm, resource, ucb_score,
  //   exploration_bonus, context_features, interaction_id }
}

export async function submitBanditFeedback({ userId, topicId, selectedArm, preMastery, postMastery }) {
  const res = await fetch(`${BASE_URL}/api/recommendations/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      topic_id: topicId,
      selected_arm: selectedArm,
      pre_mastery: preMastery,
      post_mastery: postMastery,
    }),
  })
  if (!res.ok) throw new Error('Failed to submit bandit feedback')
  return res.json()
}
