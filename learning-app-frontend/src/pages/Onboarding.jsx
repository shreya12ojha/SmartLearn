import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const userTypes = [
  { id: 'beginner_student', label: 'Student — new to this topic' },
  { id: 'experienced_student', label: 'Student — revising & leveling up' },
  { id: 'teacher', label: 'Teacher — brushing up concepts' },
]

const subjects = [
  { id: 'dsa', name: 'Data Structures & Algorithms' },
  { id: 'cn', name: 'Computer Networks' },
  { id: 'os', name: 'Operating Systems' },
  { id: 'oops', name: 'OOPs' },
  { id: 'dbms', name: 'DBMS' },
]

const levels = ['Beginner', 'Intermediate', 'Advanced']

function Onboarding({ setProfile }) {
  const [userType, setUserType] = useState('')
  const [subject, setSubject] = useState('')
  const [level, setLevel] = useState('')
  const [hours, setHours] = useState(1)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleContinue = () => {
    if (!userType || !subject || !level) {
      setError('Please answer all questions to continue.')
      return
    }
    setError('')
    setProfile({ userType, subject, level, hours })
    navigate('/quiz')
  }

  return (
    <div className="login-container onboarding-container">
      <h1>Let's personalize your path</h1>

      <div className="onboard-section">
        <label>Who are you?</label>
        <div className="choice-group">
          {userTypes.map((u) => (
            <button
              key={u.id}
              type="button"
              className={userType === u.id ? 'choice-btn selected' : 'choice-btn'}
              onClick={() => setUserType(u.id)}
            >
              {u.label}
            </button>
          ))}
        </div>
      </div>

      <div className="onboard-section">
        <label>Which topic do you want to focus on?</label>
        <div className="choice-group">
          {subjects.map((s) => (
            <button
              key={s.id}
              type="button"
              className={subject === s.id ? 'choice-btn selected' : 'choice-btn'}
              onClick={() => setSubject(s.id)}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      <div className="onboard-section">
        <label>How would you rate your current understanding?</label>
        <div className="choice-group">
          {levels.map((l) => (
            <button
              key={l}
              type="button"
              className={level === l ? 'choice-btn selected' : 'choice-btn'}
              onClick={() => setLevel(l)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      <div className="onboard-section">
        <label>How many hours can you give daily? ({hours} hr{hours > 1 ? 's' : ''})</label>
        <input
          type="range"
          min="1"
          max="8"
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="hours-slider"
        />
      </div>

      {error && <p className="form-error">{error}</p>}

      <button className="onboard-continue-btn" onClick={handleContinue}>
        Build My Roadmap
      </button>
    </div>
  )
}

export default Onboarding