import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export default function OAuthCallbackPage() {
  const { handleTokens } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState(null)
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true

    const hash = window.location.hash.startsWith('#')
      ? window.location.hash.slice(1)
      : window.location.hash
    const params = new URLSearchParams(hash)
    const err = params.get('error')
    const access = params.get('access_token')
    const refresh = params.get('refresh_token')

    if (err) {
      setError(err)
      return
    }
    if (!access || !refresh) {
      setError('Missing tokens in OAuth callback')
      return
    }

    handleTokens({ access_token: access, refresh_token: refresh })
      .then(() => {
        window.history.replaceState({}, '', '/')
        navigate('/', { replace: true })
      })
      .catch((e) => setError(e?.message || 'Failed to complete sign-in'))
  }, [handleTokens, navigate])

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h2>Sign-in failed</h2>
        <p>{error}</p>
        <a href="/login">Back to login</a>
      </div>
    )
  }
  return <div style={{ padding: 24 }}>Signing you in…</div>
}
