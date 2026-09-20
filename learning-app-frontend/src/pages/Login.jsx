import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/realApi'

function Login({ setAuth }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const validate = () => {
    if (!email.trim()) return 'Email is required.'
    if (!/^\S+@\S+\.\S+$/.test(email)) return 'Enter a valid email address.'
    if (!password) return 'Password is required.'
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
      const result = await login({ email, password })
      setAuth({ token: result.token, userId: result.user_id, email })
      navigate('/dashboard')
    } catch (err) {
      setError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-subtitle">Log in to pick up where you left off.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div className="auth-field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>

          {error && <p className="form-error">{error}</p>}

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <p className="auth-switch">
          New here? <span onClick={() => navigate('/signup')}>Create an account</span>
        </p>
      </div>
    </div>
  )
}

export default Login