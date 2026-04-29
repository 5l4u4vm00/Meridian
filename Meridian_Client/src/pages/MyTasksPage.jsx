import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, LogOut, MessageSquare, Paperclip, Pencil, Search } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import NewProjectDialog from '../components/NewProjectDialog'
import TaskDrawer from '../components/board/TaskDrawer'
import EditTaskDialog from '../components/board/EditTaskDialog'
import { useAuth } from '../auth/useAuth'
import {
  createProject as apiCreateProject,
  listProjects as apiListProjects,
} from '../api/projects'
import { listMyTasks as apiListMyTasks } from '../api/tasks'
import './board.css'
import './my-tasks.css'

const PRIORITY_STYLES = {
  high: { color: 'var(--accent)', label: 'High' },
  medium: { color: 'var(--ink-60)', label: 'Med' },
  low: { color: 'var(--ink-40)', label: 'Low' },
}

const STATUS_LABEL = {
  backlog: 'Backlog',
  in_progress: 'In Progress',
  in_review: 'In Review',
  shipped: 'Shipped',
}

function userInitials(name, email) {
  const src = (name || email || '').trim()
  if (!src) return '?'
  const parts = src.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return src.slice(0, 2).toUpperCase()
}

function startOfDay(d) {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x
}

function bucketFor(dueIso, today) {
  if (!dueIso) return 'none'
  const due = startOfDay(dueIso)
  const diffDays = Math.round((due - today) / 86400000)
  if (diffDays < 0) return 'overdue'
  if (diffDays === 0) return 'today'
  if (diffDays <= 7) return 'week'
  return 'later'
}

const BUCKETS = [
  { key: 'overdue', label: 'Overdue' },
  { key: 'today', label: 'Today' },
  { key: 'week', label: 'This Week' },
  { key: 'later', label: 'Later' },
  { key: 'none', label: 'No due date' },
]

function formatDue(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

function MyTaskRow({ task, onOpen, onEdit }) {
  const pri = PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium
  return (
    <div
      className="my-task-row"
      onClick={() => onOpen(task.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onOpen(task.id)
      }}
    >
      <div className="my-task-project" title={task.project_name}>
        <span
          className="project-dot"
          style={{ background: task.project_color }}
        />
        <span className="my-task-code">{task.code}</span>
      </div>
      <div className="my-task-title">{task.title}</div>
      <div className="my-task-tags">
        {(task.tags || []).map((t) => (
          <span key={t} className="card-tag">{t}</span>
        ))}
      </div>
      <span className="my-task-status">{STATUS_LABEL[task.status]}</span>
      <span className="my-task-counts">
        <MessageSquare size={11} strokeWidth={1.5} /> {task.comment_count ?? 0}
        <Paperclip size={11} strokeWidth={1.5} /> {task.attachment_count ?? 0}
      </span>
      <span className="priority-dot" style={{ background: pri.color }} title={pri.label} />
      <span className="my-task-due">{formatDue(task.due_date) || '—'}</span>
      <button
        type="button"
        className="card-edit-btn"
        aria-label="Edit task"
        onClick={(e) => {
          e.stopPropagation()
          onEdit(task.id)
        }}
      >
        <Pencil size={14} strokeWidth={1.6} />
      </button>
    </div>
  )
}

export default function MyTasksPage() {
  const { user, logout } = useAuth()
  const [projects, setProjects] = useState([])
  const [tasks, setTasks] = useState([])
  const [includeShipped, setIncludeShipped] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showNewProject, setShowNewProject] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [detailTaskId, setDetailTaskId] = useState(null)
  const [editTaskId, setEditTaskId] = useState(null)

  const refresh = useCallback(async (incl) => {
    const [list, p] = await Promise.all([apiListMyTasks(incl), apiListProjects()])
    setTasks(Array.isArray(list) ? list : [])
    setProjects(Array.isArray(p) ? p : [])
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        const [list, p] = await Promise.all([
          apiListMyTasks(includeShipped),
          apiListProjects(),
        ])
        if (cancelled) return
        if (!Array.isArray(list)) {
          throw new Error(
            'Unexpected response from /my-tasks — restart the backend so the new route is loaded.',
          )
        }
        setTasks(list)
        setProjects(Array.isArray(p) ? p : [])
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load tasks')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [includeShipped])

  const today = useMemo(() => startOfDay(new Date()), [])

  const grouped = useMemo(() => {
    const buckets = { overdue: [], today: [], week: [], later: [], none: [] }
    for (const t of tasks) buckets[bucketFor(t.due_date, today)].push(t)
    return buckets
  }, [tasks, today])

  const stats = useMemo(() => {
    const open = tasks.filter((t) => t.status !== 'shipped').length
    const overdue = grouped.overdue.length
    const dueWeek = grouped.today.length + grouped.week.length
    const shipped = tasks.filter((t) => t.status === 'shipped').length
    return { open, overdue, dueWeek, shipped }
  }, [tasks, grouped])

  const handleCreateProject = async (payload) => {
    await apiCreateProject(payload)
    const list = await apiListProjects()
    setProjects(list)
  }

  return (
    <div className="pm-root">
      <Sidebar
        activeKey="my-tasks"
        projects={projects}
        onNewProject={() => setShowNewProject(true)}
      />

      <main className="main">
        <div className="topbar">
          <Link to="/" className="btn back-btn">
            <ArrowLeft size={13} strokeWidth={1.8} /> Projects
          </Link>
          <div className="search">
            <Search size={14} strokeWidth={1.5} color="var(--ink-60)" />
            <input placeholder="Search tasks…" />
            <kbd>⌘K</kbd>
          </div>
          <div style={{ flex: 1 }} />
          <label className="my-tasks-toggle">
            <input
              type="checkbox"
              checked={includeShipped}
              onChange={(e) => setIncludeShipped(e.target.checked)}
            />
            <span>Include shipped</span>
          </label>
          <div className="user-menu">
            <button
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
                <button className="menu-item" onClick={logout}>
                  <LogOut size={13} strokeWidth={1.5} /> Log out
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="project-header">
          <div>
            <div className="breadcrumb">
              <span>Workspace</span>
              <span style={{ color: 'var(--ink-40)' }}>·</span>
              <span style={{ color: 'var(--ink)' }}>My Tasks</span>
            </div>
            <h1 className="serif project-title">
              My <em>Tasks</em>
            </h1>
            <div className="project-meta">
              <div className="meta-item">
                <span className="meta-label">Open</span>
                <span className="meta-value">{stats.open}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Overdue</span>
                <span className="meta-value">{stats.overdue}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Due this week</span>
                <span className="meta-value">{stats.dueWeek}</span>
              </div>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="board-loading">Loading your tasks…</div>
        ) : tasks.length === 0 ? (
          <div className="my-tasks-empty">
            Nothing assigned to you{includeShipped ? '' : ' yet'}. Open a project board to assign yourself a task.
          </div>
        ) : (
          <div className="my-tasks-list">
            {BUCKETS.map((b) => {
              const rows = grouped[b.key]
              if (!rows.length) return null
              return (
                <section key={b.key} className={`my-tasks-bucket bucket-${b.key}`}>
                  <header className="my-tasks-bucket-head">
                    <span className="my-tasks-bucket-label">{b.label}</span>
                    <span className="my-tasks-bucket-count">
                      {String(rows.length).padStart(2, '0')}
                    </span>
                  </header>
                  {rows.map((t) => (
                    <MyTaskRow
                      key={t.id}
                      task={t}
                      onOpen={(id) => setDetailTaskId(id)}
                      onEdit={(id) => setEditTaskId(id)}
                    />
                  ))}
                </section>
              )
            })}
          </div>
        )}
      </main>

      {error && (
        <div className="toast" onClick={() => setError(null)}>
          {error}
        </div>
      )}

      {showNewProject && (
        <NewProjectDialog
          onClose={() => setShowNewProject(false)}
          onCreate={handleCreateProject}
        />
      )}
      {detailTaskId != null && (
        <TaskDrawer
          key={detailTaskId}
          taskId={detailTaskId}
          onClose={() => setDetailTaskId(null)}
          onChanged={() => refresh(includeShipped)}
        />
      )}
      {editTaskId != null && (
        <EditTaskDialog
          key={editTaskId}
          taskId={editTaskId}
          onClose={() => setEditTaskId(null)}
          onSave={() => refresh(includeShipped)}
        />
      )}
    </div>
  )
}
