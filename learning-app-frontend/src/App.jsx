import { useState, useEffect } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Onboarding from './pages/Onboarding'
import Quiz from './pages/Quiz'
import Roadmap from './pages/Roadmap'
import { getStoredAuth, saveAuth } from './api/realApi'
import './App.css'

const initialMastery = {
  arrays: 0.9,
  stacks_queues: 0.85,
  linked_lists: 0.6,
  sorting: 0.45,
  trees: 0.3,
  graphs: 0.15,
}

function App() {
  const [mastery, setMastery] = useState(initialMastery)
  const [profile, setProfile] = useState(null)
  const [auth, setAuth] = useState(() => getStoredAuth()) // { token, userId }
  const [realMastery, setRealMastery] = useState({}) // { [realTopicId]: score }, DSA only

  useEffect(() => {
    if (auth) {
      saveAuth(auth)
    }
  }, [auth])


  return (
    <div>
      <nav className="navbar">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Login</NavLink>
        <NavLink to="/signup" className={({ isActive }) => isActive ? 'active' : ''}>Signup</NavLink>
        <NavLink to="/onboarding" className={({ isActive }) => isActive ? 'active' : ''}>Onboarding</NavLink>
        <NavLink to="/quiz" className={({ isActive }) => isActive ? 'active' : ''}>Quiz</NavLink>
        <NavLink to="/roadmap" className={({ isActive }) => isActive ? 'active' : ''}>Roadmap</NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Login setAuth={setAuth} />} />
        <Route path="/signup" element={<Signup setAuth={setAuth} />} />
        <Route path="/onboarding" element={<Onboarding setProfile={setProfile} />} />
        <Route
          path="/quiz"
          element={
            <Quiz
              mastery={mastery}
              setMastery={setMastery}
              profile={profile}
              auth={auth}
              realMastery={realMastery}
              setRealMastery={setRealMastery}
            />
          }
        />
        <Route
          path="/roadmap"
          element={
            <Roadmap
              mastery={mastery}
              profile={profile}
              auth={auth}
              realMastery={realMastery}
            />
          }
        />
      </Routes>
    </div>
  )
}

export default App