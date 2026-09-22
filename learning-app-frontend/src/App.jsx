import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Onboarding from './pages/Onboarding'
import Quiz from './pages/Quiz'
import Roadmap from './pages/Roadmap'
import Dashboard from './pages/Dashboard'
import { fetchTopicGraph, fetchMastery } from './api/realApi'
import './App.css'

const initialMastery = {
  arrays: 0.9,
  stacks_queues: 0.85,
  linked_lists: 0.6,
  sorting: 0.45,
  trees: 0.3,
  graphs: 0.15,
}

// Same topological sort used inside RealDsaQuiz — kept here too so the
// Dashboard's topic list (including untouched, 0-mastery topics) respects
// prerequisite order, not just database insertion order.
function topoSortTopics(topics, prerequisites) {
  const ids = topics.map((t) => t.id)
  const idSet = new Set(ids)
  const inDegree = {}
  const adj = {}
  ids.forEach((id) => {
    inDegree[id] = 0
    adj[id] = []
  })
  prerequisites.forEach((p) => {
    if (idSet.has(p.topic_id) && idSet.has(p.prerequisite_topic_id)) {
      adj[p.prerequisite_topic_id].push(p.topic_id)
      inDegree[p.topic_id] += 1
    }
  })
  const queue = ids.filter((id) => inDegree[id] === 0)
  const order = []
  while (queue.length) {
    const id = queue.shift()
    order.push(id)
    adj[id].forEach((next) => {
      inDegree[next] -= 1
      if (inDegree[next] === 0) queue.push(next)
    })
  }
  ids.forEach((id) => {
    if (!order.includes(id)) order.push(id)
  })
  return order.map((id) => topics.find((t) => t.id === id))
}

function AppRoutes() {
  const [mastery, setMastery] = useState(initialMastery)
  const [profile, setProfile] = useState(null)
  const [auth, setAuth] = useState(null)
  const [realMastery, setRealMastery] = useState({})   // { topic_id: score }
  const [realTopics, setRealTopics] = useState([])       // [{ id, name }] in prerequisite order
  const location = useLocation()

  const hideNav = !(auth && profile) || location.pathname === '/dashboard'

  // Once logged in, load the real DSA topic list (ordered) and the
  // student's current real mastery — this feeds both Dashboard and,
  // going forward, keeps things in sync without each page re-fetching separately.
  useEffect(() => {
    if (!auth?.userId) return

    fetchTopicGraph().then((graphData) => {
      const dsaTopics = graphData.topics.filter((t) => (t.domain || '').toLowerCase() === 'dsa')
      const ordered = topoSortTopics(dsaTopics, graphData.prerequisites)
      setRealTopics(ordered.map((t) => ({ id: t.id, name: t.name })))
    })

    fetchMastery(auth.userId).then((data) => {
      const masteryDict = {}
      ;(data.mastery || []).forEach((m) => {
        masteryDict[m.topic_id] = m.mastery_score
      })
      setRealMastery(masteryDict)
    })
  }, [auth])

  return (
    <div>
      {!hideNav && (
        <nav className="navbar">
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
          <NavLink to="/quiz" className={({ isActive }) => isActive ? 'active' : ''}>Quiz</NavLink>
          <NavLink to="/roadmap" className={({ isActive }) => isActive ? 'active' : ''}>Roadmap</NavLink>
        </nav>
      )}

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login setAuth={setAuth} />} />
        <Route path="/signup" element={<Signup setAuth={setAuth} />} />
        <Route path="/onboarding" element={<Onboarding setProfile={setProfile} />} />
        <Route
          path="/quiz"
          element={
            <Quiz
              mastery={mastery}
              setMastery={setMastery}
              realMastery={realMastery}
              setRealMastery={setRealMastery}
              profile={profile}
              auth={auth}
            />
          }
        />
        <Route
          path="/roadmap"
          element={
            <Roadmap
              mastery={mastery}
              profile={profile}
              realTopics={realTopics}
              realMastery={realMastery}
              auth={auth}
            />
          }
        />
        <Route
          path="/dashboard"
          element={
            <Dashboard
              mastery={mastery}
              realMastery={realMastery}
              realTopics={realTopics}
              profile={profile}
              auth={auth}
              setAuth={setAuth}
              setProfile={setProfile}
            />
          }
        />
      </Routes>
    </div>
  )
}

function App() {
  return <AppRoutes />
}

export default App