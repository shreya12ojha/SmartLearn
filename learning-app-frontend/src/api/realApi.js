const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// ============================================================
// Auth Storage Helpers (Existing Auth System Persistence)
// ============================================================

export function getStoredAuth() {
  try {
    const raw = localStorage.getItem('smartlearn_auth')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed && (parsed.token || parsed.userId || parsed.user_id)) {
        const userId = parsed.userId ?? parsed.user_id ?? parsed.user?.id
        return {
          token: parsed.token || '',
          userId: userId ? Number(userId) : null,
          user_id: userId ? Number(userId) : null,
          user: parsed.user || null,
        }
      }
    }
    const token = localStorage.getItem('smartlearn_token') || localStorage.getItem('token')
    const rawUserId = localStorage.getItem('smartlearn_user_id') || localStorage.getItem('userId') || localStorage.getItem('user_id')
    if (token || rawUserId) {
      const userId = rawUserId ? Number(rawUserId) : null
      return {
        token: token || '',
        userId,
        user_id: userId,
        user: null,
      }
    }
  } catch (e) {
    console.warn('Failed to read auth from localStorage:', e)
  }
  return null
}

export function saveAuth(auth) {
  if (!auth) {
    clearAuth()
    return
  }
  const token = auth.token || auth.access_token || ''
  const userId = auth.userId ?? auth.user_id ?? auth.user?.id ?? null
  const payload = {
    token,
    userId: userId ? Number(userId) : null,
    user_id: userId ? Number(userId) : null,
    user: auth.user || null,
  }
  try {
    localStorage.setItem('smartlearn_auth', JSON.stringify(payload))
    if (token) localStorage.setItem('smartlearn_token', token)
    if (userId) localStorage.setItem('smartlearn_user_id', String(userId))
  } catch (e) {
    console.warn('Failed to save auth to localStorage:', e)
  }
}

export function clearAuth() {
  try {
    localStorage.removeItem('smartlearn_auth')
    localStorage.removeItem('smartlearn_token')
    localStorage.removeItem('smartlearn_user_id')
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('user_id')
  } catch (e) {
    console.warn('Failed to clear auth from localStorage:', e)
  }
}

function getAuthHeader(token = null) {
  const currentToken = token || getStoredAuth()?.token
  return currentToken ? { Authorization: `Bearer ${currentToken}` } : {}
}

async function handleResponse(res, defaultError = 'Request failed') {
  if (!res.ok) {
    let errorDetail = ''
    try {
      const err = await res.json()
      errorDetail = err.detail || err.message || ''
    } catch {
      // response wasn't JSON
    }

    const err = new Error(
      errorDetail ||
      (res.status === 401
        ? 'Authentication required: Your session has expired or is invalid.'
        : res.status === 403
        ? 'Forbidden: You do not have permission to access this resource.'
        : res.status === 404
        ? 'Resource not found in database.'
        : res.status >= 500
        ? `Internal server error (${res.status}): Please check backend logs.`
        : `${defaultError} (${res.status})`)
    )
    err.status = res.status
    err.detail = errorDetail
    throw err
  }
  return res.json()
}

// ============================================================
// Authentication Endpoints
// ============================================================

export async function signup({ name, email, password }) {
  const res = await fetch(`${BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  })
  const data = await handleResponse(res, 'Signup failed')
  if (data?.token && data?.user_id) {
    saveAuth({ token: data.token, userId: data.user_id, user_id: data.user_id })
  }
  return data // { token, user_id }
}

export async function login({ email, password }) {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  const data = await handleResponse(res, 'Login failed')
  if (data?.token && data?.user_id) {
    saveAuth({ token: data.token, userId: data.user_id, user_id: data.user_id })
  }
  return data // { token, user_id }
}

// ============================================================
// Quiz & Concept Graph Endpoints
// ============================================================

export async function fetchTopicGraph() {
  const res = await fetch(`${BASE_URL}/api/quiz/topics/graph`)
  return handleResponse(res, 'Failed to fetch topic graph')
}

export async function fetchQuizQuestions(topicId) {
  const res = await fetch(`${BASE_URL}/api/quiz?topic=${topicId}`)
  return handleResponse(res, 'Failed to fetch quiz questions')
}

export async function submitQuizReal(userId, answers, token = null) {
  const res = await fetch(`${BASE_URL}/api/quiz/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(token),
    },
    body: JSON.stringify({ user_id: Number(userId), answers }),
  })
  return handleResponse(res, 'Submit quiz failed')
}

// ============================================================
// Path Planning & Next Topic Endpoints
// ============================================================

export async function fetchRoadmapReal(userId, token = null) {
  const res = await fetch(`${BASE_URL}/api/path-planning/roadmap/${userId}`, {
    headers: {
      ...getAuthHeader(token),
    },
  })
  return handleResponse(res, 'Failed to fetch roadmap')
}

export async function fetchNextTopicReal(userId, token = null) {
  const res = await fetch(`${BASE_URL}/api/path-planning/next-topic/${userId}`, {
    headers: {
      ...getAuthHeader(token),
    },
  })
  return handleResponse(res, 'Failed to fetch next topic')
}

// ============================================================
// CMAB / LinUCB Recommendation & Feedback Endpoints
// ============================================================

export async function fetchResourceRecommendation(userId, topicId, token = null) {
  const res = await fetch(
    `${BASE_URL}/api/recommendations/resource?user_id=${userId}&topic_id=${topicId}`,
    {
      headers: {
        ...getAuthHeader(token),
      },
    }
  )
  return handleResponse(res, 'Failed to fetch resource recommendation')
}

export async function submitBanditFeedback(
  { userId, topicId, selectedArm, preMastery, postMastery },
  token = null
) {
  const res = await fetch(`${BASE_URL}/api/recommendations/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(token),
    },
    body: JSON.stringify({
      user_id: Number(userId),
      topic_id: Number(topicId),
      selected_arm: selectedArm,
      pre_mastery: Number(preMastery),
      post_mastery: Number(postMastery),
    }),
  })
  return handleResponse(res, 'Failed to submit bandit feedback')
}

export async function fetchResources(topicId = null, format = null) {
  const params = new URLSearchParams()
  if (topicId) params.append('topic_id', topicId)
  if (format) params.append('format', format)
  const query = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`${BASE_URL}/api/resources${query}`)
  return handleResponse(res, 'Failed to fetch resources')
}