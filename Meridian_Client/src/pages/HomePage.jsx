import { useAuth } from '../auth/useAuth'
import './auth.css'

export default function HomePage() {
  const { user, logout } = useAuth()
  return (
    <div className="home-shell">
      <h1>Welcome, {user?.name || user?.email}</h1>
      <p>You're signed in as <code>{user?.email}</code>.</p>
      {user?.role && <p>Role: <code>{user.role}</code></p>}
      <button className="auth-submit" onClick={logout}>
        Log out
      </button>
    </div>
  )
}
