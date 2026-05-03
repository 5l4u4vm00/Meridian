import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArchiveRestore, LogOut } from 'lucide-react'
import {
  listProjects as apiListProjects,
  updateProject as apiUpdateProject,
} from '../api/projects'
import { useAuth } from '../auth/useAuth'
import { relativeTime } from '../utils/time'
import './board.css'
import './projects.css'

function userInitials(name, email) {
  const src = (name || email || '').trim()
  if (!src) return '?'
  const parts = src.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return src.slice(0, 2).toUpperCase()
}

export default function ArchivePage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busyCode, setBusyCode] = useState(null)
  const [actionError, setActionError] = useState(null)

  const refresh = async () => {
    const list = await apiListProjects({ archived: true })
    setProjects(list)
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        const list = await apiListProjects({ archived: true })
        if (!cancelled) setProjects(list)
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load archive')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const sorted = useMemo(
    () =>
      [...projects].sort((a, b) => {
        const ta = a.last_activity ? new Date(a.last_activity).getTime() : 0
        const tb = b.last_activity ? new Date(b.last_activity).getTime() : 0
        return tb - ta
      }),
    [projects],
  )

  const unarchive = async (code) => {
    setBusyCode(code)
    setActionError(null)
    try {
      await apiUpdateProject(code, { is_archived: false })
      await refresh()
    } catch (e) {
      setActionError(e.message || 'Failed to unarchive project')
    } finally {
      setBusyCode(null)
    }
  }

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
          <h1 className="projects-title serif">Archive</h1>
          <div className="projects-meta">
            {loading ? 'Loading…' : `${projects.length} archived`}
          </div>
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => navigate('/')}
        >
          <ArrowLeft size={14} strokeWidth={1.5} />
          <span>Back to projects</span>
        </button>
      </section>

      {error && <div className="projects-error">{error}</div>}
      {actionError && <div className="projects-error">{actionError}</div>}

      {!loading && !error && sorted.length === 0 && (
        <div className="projects-empty">No archived projects.</div>
      )}

      {sorted.length > 0 && (
        <table className="projects-table">
          <thead>
            <tr>
              <th className="col-header">Code</th>
              <th className="col-header">Name</th>
              <th className="col-header">Tasks</th>
              <th className="col-header">Last activity</th>
              <th className="col-header" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr key={p.id} className="project-row-tr">
                <td className="col-code">
                  <span
                    className="project-dot"
                    style={{ background: p.color }}
                  />
                  <span className="project-card-code">{p.code}</span>
                </td>
                <td className="col-name serif">{p.name}</td>
                <td className="col-tasks">{p.task_count ?? 0}</td>
                <td className="col-activity">
                  {p.last_activity ? relativeTime(p.last_activity) : '—'}
                </td>
                <td className="col-activity">
                  <button
                    type="button"
                    className="btn"
                    disabled={busyCode === p.code}
                    onClick={() => unarchive(p.code)}
                  >
                    <ArchiveRestore size={13} strokeWidth={1.5} />
                    <span>Unarchive</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
