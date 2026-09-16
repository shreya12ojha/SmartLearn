import { useLocation } from 'react-router-dom'
import MockQuiz from './MockQuiz'
import RealDsaQuiz from './RealDsaQuiz'

function Quiz(props) {
  const { profile, realMastery, setRealMastery, auth } = props
  const location = useLocation()
  const startAt = location.state?.startAt
  const subject = startAt?.subject || profile?.subject

  if (subject === 'dsa') {
    return <RealDsaQuiz mastery={realMastery} setMastery={setRealMastery} auth={auth} />
  }
  return <MockQuiz {...props} />
}

export default Quiz