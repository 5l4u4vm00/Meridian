import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, LogOut } from 'lucide-react'
import {
  listMembers as apiListMembers,
  listProjects as apiListProjects,
} from '../api/projects'
import { useAuth } from '../auth/useAuth'
import './board.css'
import './projects.css'

function userInitials(name, email) {
  const src = (name || email || '').trim()
  if (!src) return '?'
  const parts = src.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return src.slice(0, 2).toUpperCase()
}

function roleLabel(role) {
  if (role === 'lead') return 'Lead'
  if (role === 'member') return 'Member'
  return '—'
}

export default function TeamPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
      ; (async () => {
        try {
          setLoading(true)
          const projects = await apiListProjects()
          const membersByProject = await Promise.all(
            projects.map((p) => apiListMembers(p.code).catch(() => [])),
          )
          if (cancelled) return
          setGroups(
            projects.map((project, i) => ({
              project,
              members: membersByProject[i] || [],
            })),
          )
        } catch (e) {
          if (!cancelled) setError(e.message || 'Failed to load team')
        } finally {
          if (!cancelled) setLoading(false)
        }
      })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="projects-page">
      <header className="projects-brand">
        <div className="brand">
          <span className="brand-mark">Meridian</span>
        </div>
        <div className="brand-sub">A Project Studio</div>
        <div className="brand-rule" />
        <div className="user-menu">
          <button
            type="button"
            className="avatar accent"
            onClick={() => setUserMenuOpen((v) => !v)}
            aria-label="Account menu"
          >
            {userInitials(user?.name, user?.email)}
          </button>
          {userMenuOpen && (
            <div className="menu" onMouseLeave={() => setUserMenuOpen(false)}>
              <div className="menu-head">
                <div className="menu-name">{user?.name || user?.email}</div>
                <div className="menu-email">{user?.email}</div>
              </div>
              <button type="button" className="menu-item" onClick={logout}>
                <LogOut size={13} strokeWidth={1.5} /> Log out
              </button>
            </div>
          )}
        </div>
      </header>

      <section className="projects-title-row">
        <div>
          <h1 className="projects-title serif">Team</h1>
          <div className="projects-meta">
            {loading ? 'Loading…' : `${groups.length} project${groups.length === 1 ? '' : 's'}`}
          </div>
        </div>
        <button type="button" className="btn" onClick={() => navigate('/board')}>
          <ArrowLeft size={14} strokeWidth={1.5} />
          <span>Back</span>
        </button>
      </section>

      {error && <div className="projects-error">{error}</div>}

      {!loading && !error && groups.length === 0 && (
        <div className="projects-empty">No projects.</div>
      )}

      {groups.map(({ project, members }) => (
        <section
          key={project.id}
          style={{ marginTop: 24 }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              marginBottom: 8,
            }}
          >
            <span
              className="project-dot"
              style={{ background: project.color }}
            />
            <span className="project-card-code">{project.code}</span>
            <span className="serif" style={{ fontSize: 16 }}>
              {project.name}
            </span>
          </div>

          {members.length === 0 ? (
            <div className="projects-empty">No members.</div>
          ) : (
            <table className="projects-table">
              <thead>
                <tr>
                  <th className="col-header">Member</th>
                  <th className="col-header">Email</th>
                  <th className="col-header">Role</th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => (
                  <tr key={m.id} className="project-row-tr">
                    <td className="col-name">
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 8,
                        }}
                      >
                        <span className="avatar accent" style={{ width: 22, height: 22, fontSize: 11 }}>
                          {userInitials(m.name, m.email)}
                        </span>
                        <span>{m.name || '—'}</span>
                      </span>
                    </td>
                    <td className="col-activity" style={{ color: 'var(--ink-40)' }}>
                      {m.email}
                    </td>
                    <td className="col-activity">{roleLabel(m.role)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ))}
    </div>
  )
}
