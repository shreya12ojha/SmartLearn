import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { signup } from '../api/realApi'

function Signup({ setAuth }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [dob, setDob] = useState('')
  const [college, setCollege] = useState('')
  const [mobile, setMobile] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const validate = () => {
    if (!name.trim()) return 'Name is required.'
    if (!email.trim()) return 'Email is required.'
    if (!/^\S+@\S+\.\S+$/.test(email)) return 'Enter a valid email address.'
    if (password.length < 6) return 'Password must be at least 6 characters.'
    if (!dob) return 'Date of birth is required.'
    if (!college.trim()) return 'College/University name is required.'
    if (!/^\d{10}$/.test(mobile)) return 'Enter a valid 10-digit mobile number.'
    return ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setLoading(true)
    try {
      // NOTE: backend SignupRequest currently only accepts name/email/password.
      // dob/college/mobile are held in frontend state for now (see setAuth below)
      // until the backend schema + endpoint are extended to store them.
      const result = await signup({ name, email, password })
      setAuth({
        token: result.token,
        userId: result.user_id,
        name,
        email,
        dob,
        college,
        mobile,
      })
      navigate('/onboarding')
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">Set up your profile to get a roadmap built for you.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-row">
            <div className="auth-field">
              <label>Full Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Aashi Singh" />
            </div>
            <div className="auth-field">
              <label>Date of Birth</label>
              <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
            </div>
          </div>

          <div className="auth-field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>

          <div className="auth-row">
            <div className="auth-field">
              <label>Mobile Number</label>
              <input type="tel" value={mobile} onChange={(e) => setMobile(e.target.value)} placeholder="9876543210" maxLength={10} />
            </div>
            <div className="auth-field">
              <label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
            </div>
          </div>

          <div className="auth-field">
            <label>College / University</label>
            <input type="text" value={college} onChange={(e) => setCollege(e.target.value)} placeholder="e.g. VIT Pune" />
          </div>

          {error && <p className="form-error">{error}</p>}

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <span onClick={() => navigate('/login')}>Log in</span>
        </p>
      </div>
    </div>
  )
}

export default Signup