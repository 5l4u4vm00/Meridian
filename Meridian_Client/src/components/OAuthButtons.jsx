const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export default function OAuthButtons() {
  return (
    <div className="oauth-buttons">
      <a className="oauth-btn" href={`${API_BASE}/auth/google/login`}>
        Continue with Google
      </a>
      <a className="oauth-btn" href={`${API_BASE}/auth/github/login`}>
        Continue with GitHub
      </a>
    </div>
  )
}
