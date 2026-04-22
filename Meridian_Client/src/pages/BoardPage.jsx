import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Archive,
  ArrowUpRight,
  Calendar,
  ChevronRight,
  Filter,
  Inbox,
  Layers,
  LogOut,
  MessageSquare,
  MoreHorizontal,
  Paperclip,
  Plus,
  Search,
  Settings,
  TrendingUp,
  Users,
  X,
} from 'lucide-react'
import { useAuth } from '../auth/useAuth'
import {
  createProject as apiCreateProject,
  listProjects as apiListProjects,
} from '../api/projects'
import {
  createTask as apiCreateTask,
  listBoard as apiListBoard,
  moveTask as apiMoveTask,
} from '../api/tasks'
import {
  getActivity as apiGetActivity,
  getStats as apiGetStats,
  getWorkload as apiGetWorkload,
} from '../api/activity'
import './board.css'

const STATUS_ORDER = ['backlog', 'in_progress', 'in_review', 'shipped']
const STATUS_LABEL = {
  backlog: 'Backlog',
  in_progress: 'In Progress',
  in_review: 'In Review',
  shipped: 'Shipped',
}
const PRIORITY_STYLES = {
  high: { color: 'var(--accent)', label: 'High' },
  medium: { color: 'var(--ink-60)', label: 'Med' },
  low: { color: 'var(--ink-40)', label: 'Low' },
}

const DEFAULT_COLORS = ['#c4511c', '#2d4a3e', '#3d3d5c', '#8a6d3b']

function userInitials(name, email) {
  const src = (name || email || '').trim()
  if (!src) return '?'
  const parts = src.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return src.slice(0, 2).toUpperCase()
}

function formatDue(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

function relativeTime(iso) {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  const delta = Math.max(0, Date.now() - t)
  const s = Math.floor(delta / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d}d`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

const VERB_PHRASE = {
  created: 'created',
  updated: 'updated',
  moved: 'moved',
  completed: 'completed',
  commented: 'commented on',
  attached: 'attached to',
}

function activityVerbPhrase(event) {
  return VERB_PHRASE[event.verb] || event.verb
}

function ColumnTitle({ title }) {
  if (title === 'In Progress') {
    return (
      <>
        In <em>Progress</em>
      </>
    )
  }
  if (title === 'Shipped') return <em>{title}</em>
  return title
}

function TaskCard({ task, onDragStart, isDragging }) {
  const pri = PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium
  return (
    <div
      className="card"
      data-task-id={task.id}
      draggable
      onDragStart={(e) => onDragStart(e, task)}
      style={{ opacity: isDragging ? 0.4 : 1 }}
    >
      <div className="card-top">
        <span className="card-id">{task.code}</span>
        <span className="priority-dot" style={{ background: pri.color }} title={pri.label} />
      </div>
      <div className="card-title">{task.title}</div>
      {task.tags?.length > 0 && (
        <div className="card-tags">
          {task.tags.map((t) => (
            <span key={t} className="card-tag">
              {t}
            </span>
          ))}
        </div>
      )}
      <div className="card-footer">
        <div className="card-footer-left">
          <span>
            <MessageSquare size={10} strokeWidth={1.5} /> 0
          </span>
          <span>
            <Paperclip size={10} strokeWidth={1.5} /> 0
          </span>
          {task.assignee_initials && (
            <div
              className="avatar"
              style={{ width: 20, height: 20, fontSize: 8.5, marginLeft: 2 }}
            >
              {task.assignee_initials}
            </div>
          )}
        </div>
        {task.due_date && <span className="card-due">{formatDue(task.due_date)}</span>}
      </div>
    </div>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <span className="serif modal-title">{title}</span>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <X size={14} strokeWidth={1.5} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function NewProjectDialog({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [color, setColor] = useState(DEFAULT_COLORS[0])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onCreate({ name: name.trim(), code: code.trim().toUpperCase(), color })
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to create project')
      setSubmitting(false)
    }
  }

  return (
    <Modal title="New project" onClose={onClose}>
      <form onSubmit={submit} className="modal-body">
        <label className="field">
          <span className="field-label">Name</span>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Meridian Rebrand"
            required
          />
        </label>
        <label className="field">
          <span className="field-label">Code</span>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="MRD"
            pattern="[A-Z0-9]{2,8}"
            title="2–8 uppercase letters or digits"
            required
          />
        </label>
        <label className="field">
          <span className="field-label">Color</span>
          <div className="color-row">
            {DEFAULT_COLORS.map((c) => (
              <button
                key={c}
                type="button"
                className={`color-swatch ${color === c ? 'selected' : ''}`}
                style={{ background: c }}
                onClick={() => setColor(c)}
                aria-label={`color ${c}`}
              />
            ))}
          </div>
        </label>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={submitting}>
            Create project
          </button>
        </div>
      </form>
    </Modal>
  )
}

function NewTaskDialog({ initialStatus, onClose, onCreate }) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState('medium')
  const [tags, setTags] = useState('')
  const [status, setStatus] = useState(initialStatus)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onCreate({
        title: title.trim(),
        priority,
        status,
        tags: tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      })
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to create task')
      setSubmitting(false)
    }
  }

  return (
    <Modal title="New task" onClose={onClose}>
      <form onSubmit={submit} className="modal-body">
        <label className="field">
          <span className="field-label">Title</span>
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Audit typography system"
            required
          />
        </label>
        <div className="field-row">
          <label className="field">
            <span className="field-label">Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUS_ORDER.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABEL[s]}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Priority</span>
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
        </div>
        <label className="field">
          <span className="field-label">Tags (comma-separated)</span>
          <input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="identity, review"
          />
        </label>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={submitting}>
            Create task
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function BoardPage() {
  const { user, logout } = useAuth()

  const [projects, setProjects] = useState([])
  const [activeCode, setActiveCode] = useState(null)
  const [board, setBoard] = useState(null)
  const [stats, setStats] = useState(null)
  const [workload, setWorkload] = useState([])
  const [activity, setActivity] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showNewProject, setShowNewProject] = useState(false)
  const [newTaskStatus, setNewTaskStatus] = useState(null)
  const [draggingId, setDraggingId] = useState(null)
  const [dragOverStatus, setDragOverStatus] = useState(null)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const activeProject = useMemo(
    () => projects.find((p) => p.code === activeCode) || null,
    [projects, activeCode],
  )

  const refreshProjects = useCallback(async () => {
    const list = await apiListProjects()
    setProjects(list)
    if (list.length > 0 && !list.find((p) => p.code === activeCode)) {
      setActiveCode(list[0].code)
    }
    return list
  }, [activeCode])

  const refreshBoard = useCallback(async (code) => {
    if (!code) {
      setBoard(null)
      setStats(null)
      setWorkload([])
      setActivity([])
      return
    }
    const [b, s, w, a] = await Promise.all([
      apiListBoard(code),
      apiGetStats(code).catch(() => null),
      apiGetWorkload(code).catch(() => []),
      apiGetActivity(code).catch(() => []),
    ])
    setBoard(b)
    setStats(s)
    setWorkload(w)
    setActivity(a)
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        const list = await apiListProjects()
        if (cancelled) return
        setProjects(list)
        setActiveCode(list[0]?.code || null)
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load projects')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!activeCode) return undefined
    let cancelled = false
    ;(async () => {
      try {
        const [b, s, w, a] = await Promise.all([
          apiListBoard(activeCode),
          apiGetStats(activeCode).catch(() => null),
          apiGetWorkload(activeCode).catch(() => []),
          apiGetActivity(activeCode).catch(() => []),
        ])
        if (cancelled) return
        setBoard(b)
        setStats(s)
        setWorkload(w)
        setActivity(a)
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load board')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [activeCode])

  const handleCreateProject = async (payload) => {
    await apiCreateProject(payload)
    const list = await apiListProjects()
    setProjects(list)
    setActiveCode(payload.code)
  }

  const handleCreateTask = async (payload) => {
    await apiCreateTask(activeCode, payload)
    await refreshBoard(activeCode)
    await refreshProjects()
  }

  const dropAnchors = (columnEl, movingId, clientY) => {
    const cards = Array.from(columnEl.querySelectorAll('[data-task-id]')).filter(
      (el) => Number(el.dataset.taskId) !== movingId,
    )
    let before = null
    let after = null
    for (const el of cards) {
      const rect = el.getBoundingClientRect()
      const mid = rect.top + rect.height / 2
      if (clientY >= mid) {
        before = Number(el.dataset.taskId)
      } else {
        after = Number(el.dataset.taskId)
        break
      }
    }
    return { before_task_id: before, after_task_id: after }
  }

  const onDragStart = (e, task) => {
    setDraggingId(task.id)
    e.dataTransfer.setData('text/plain', String(task.id))
    e.dataTransfer.effectAllowed = 'move'
  }

  const onColumnDragOver = (e, status) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverStatus(status)
  }

  const onColumnDrop = async (e, status) => {
    e.preventDefault()
    setDragOverStatus(null)
    const id = Number(e.dataTransfer.getData('text/plain'))
    setDraggingId(null)
    if (!id || !board) return
    const source = board.columns
      .flatMap((c) => c.tasks)
      .find((t) => t.id === id)
    if (!source) return

    const columnEl = e.currentTarget
    const { before_task_id, after_task_id } = dropAnchors(columnEl, id, e.clientY)

    // No-op: dropped into same column at its existing neighbors.
    if (
      source.status === status &&
      before_task_id === null &&
      after_task_id === null
    ) {
      return
    }

    // Optimistic reorder: drop the card between the chosen anchors.
    setBoard((prev) => {
      if (!prev) return prev
      const moved = { ...source, status }
      return {
        columns: prev.columns.map((col) => {
          const without = col.tasks.filter((t) => t.id !== id)
          if (col.status !== status) return { ...col, tasks: without }
          const next = []
          let inserted = false
          for (const t of without) {
            if (!inserted && after_task_id === t.id) {
              next.push(moved)
              inserted = true
            }
            next.push(t)
            if (!inserted && before_task_id === t.id) {
              next.push(moved)
              inserted = true
            }
          }
          if (!inserted) next.push(moved)
          return { ...col, tasks: next }
        }),
      }
    })

    try {
      await apiMoveTask(id, { status, before_task_id, after_task_id })
      await refreshBoard(activeCode)
    } catch (err) {
      setError(err.message || 'Failed to move task')
      await refreshBoard(activeCode)
    }
  }

  if (loading) {
    return <div className="board-loading">Loading your workspace…</div>
  }

  if (projects.length === 0) {
    return (
      <div className="board-empty">
        <div>
          <div className="brand">
            <span className="brand-mark">Folio</span>
            <span className="brand-sub">/ 01</span>
          </div>
          <h2 className="serif empty-title">
            Start your <em>first project.</em>
          </h2>
          <p className="empty-sub">
            Projects group tasks. Give yours a name and a short code like{' '}
            <span className="mono">MRD</span> for task IDs.
          </p>
          <button className="btn primary" onClick={() => setShowNewProject(true)}>
            <Plus size={13} strokeWidth={1.8} /> New project
          </button>
          <button className="btn ghost logout" onClick={logout}>
            <LogOut size={13} strokeWidth={1.5} /> Log out
          </button>
        </div>
        {showNewProject && (
          <NewProjectDialog
            onClose={() => setShowNewProject(false)}
            onCreate={handleCreateProject}
          />
        )}
      </div>
    )
  }

  const columns = board?.columns || STATUS_ORDER.map((status) => ({ status, tasks: [] }))

  return (
    <div className="pm-root">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">Folio</span>
          <span className="brand-sub">/ 04</span>
        </div>
        <div className="brand-sub">A Project Studio</div>
        <div className="brand-rule" />

        <div className="sidebar-section">
          <div className="section-label">
            <span>Workspace</span>
            <span className="section-label-num">i.</span>
          </div>
          {[
            { icon: Inbox, label: 'Inbox', count: null },
            { icon: Layers, label: 'My Tasks', count: null },
            { icon: Calendar, label: 'Calendar', count: null },
            { icon: TrendingUp, label: 'Insights', count: null },
          ].map((item) => (
            <div key={item.label} className="nav-item">
              <item.icon size={14} strokeWidth={1.5} />
              <span>{item.label}</span>
              {item.count !== null && <span className="count">{item.count}</span>}
            </div>
          ))}
        </div>

        <div className="sidebar-section">
          <div className="section-label">
            <span>Projects</span>
            <span className="section-label-num">ii.</span>
          </div>
          {projects.map((p) => (
            <div
              key={p.id}
              className={`project-row ${activeCode === p.code ? 'active' : ''}`}
              onClick={() => setActiveCode(p.code)}
            >
              <div className="project-dot" style={{ background: p.color }} />
              <span className="project-name">{p.name}</span>
              <span className="project-code">{p.code}</span>
            </div>
          ))}
          <div
            className="nav-item"
            style={{ color: 'var(--ink-40)', marginTop: 4, cursor: 'pointer' }}
            onClick={() => setShowNewProject(true)}
          >
            <Plus size={13} strokeWidth={1.5} />
            <span style={{ fontSize: 12 }}>New project</span>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-label">
            <span>Library</span>
            <span className="section-label-num">iii.</span>
          </div>
          {[
            { icon: Users, label: 'Team' },
            { icon: Archive, label: 'Archive' },
            { icon: Settings, label: 'Settings' },
          ].map((item) => (
            <div key={item.label} className="nav-item">
              <item.icon size={14} strokeWidth={1.5} />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div className="search">
            <Search size={14} strokeWidth={1.5} color="var(--ink-60)" />
            <input placeholder="Search tasks, projects, people…" />
            <kbd>⌘K</kbd>
          </div>
          <div style={{ flex: 1 }} />
          <button className="btn primary" onClick={() => setNewTaskStatus('backlog')}>
            <Plus size={13} strokeWidth={1.8} /> New task
          </button>
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
              <span>Studio</span>
              <ChevronRight size={11} strokeWidth={1.5} />
              <span>{activeProject?.code}</span>
              <ChevronRight size={11} strokeWidth={1.5} />
              <span style={{ color: 'var(--ink)' }}>Board</span>
            </div>
            <h1 className="serif project-title">
              {activeProject?.name?.split(' ').slice(0, -1).join(' ')}{' '}
              <em>{activeProject?.name?.split(' ').slice(-1)}</em>
            </h1>
            <div className="project-meta">
              <div className="meta-item">
                <span className="meta-label">Tasks</span>
                <span className="meta-value">
                  {columns.reduce((n, c) => n + c.tasks.length, 0)} total
                </span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Shipped</span>
                <span className="meta-value">
                  {columns.find((c) => c.status === 'shipped')?.tasks.length || 0}
                </span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Lead</span>
                <span className="meta-value">{user?.name || '—'}</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button className="btn">
              Share <ArrowUpRight size={13} strokeWidth={1.5} />
            </button>
            <button className="btn">
              <MoreHorizontal size={13} strokeWidth={1.5} />
            </button>
          </div>
        </div>

        <div className="toolbar">
          <button className="chip">
            <Filter size={11} strokeWidth={1.5} /> Filter
          </button>
          <button className="chip">Group: Status</button>
          <button className="chip">Sort: Priority</button>
          <div style={{ flex: 1 }} />
          <span className="toolbar-stamp">LIVE · API</span>
        </div>

        <div className="board">
          {columns.map((col) => (
            <div
              key={col.status}
              className={`column ${dragOverStatus === col.status ? 'drag-over' : ''}`}
              onDragOver={(e) => onColumnDragOver(e, col.status)}
              onDragLeave={() => setDragOverStatus(null)}
              onDrop={(e) => onColumnDrop(e, col.status)}
            >
              <div className="column-head">
                <div className="column-title">
                  <ColumnTitle title={STATUS_LABEL[col.status]} />
                </div>
                <span className="column-count">
                  {String(col.tasks.length).padStart(2, '0')}
                </span>
              </div>

              {col.tasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onDragStart={onDragStart}
                  isDragging={draggingId === task.id}
                />
              ))}

              <button
                className="add-card"
                onClick={() => setNewTaskStatus(col.status)}
              >
                + Add card
              </button>
            </div>
          ))}
        </div>
      </main>

      <aside className="right-panel">
        <div className="panel-title">Today, at a glance</div>
        <div className="panel-date">
          {new Date()
            .toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: '2-digit',
              year: '2-digit',
            })
            .toUpperCase()
            .replace(/,/g, ' ·')}
        </div>
        <div className="panel-rule" />

        <div className="stat-grid">
          <div className="stat">
            <div className="stat-label">Open</div>
            <div className="stat-value">{stats?.open ?? '—'}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Shipped</div>
            <div className="stat-value">{stats?.shipped ?? '—'}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Overdue</div>
            <div className="stat-value">{stats?.overdue ?? '—'}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Velocity</div>
            <div className="stat-value">{stats?.velocity ?? '—'}</div>
          </div>
        </div>

        <div className="section-label">
          <span>Team Load</span>
          <span className="section-label-num">i.</span>
        </div>
        {workload.length === 0 ? (
          <div className="placeholder-note">No assigned tasks yet.</div>
        ) : (
          workload.map((m) => (
            <div key={m.user_id} className="team-row">
              <div className="avatar">{m.initials}</div>
              <div className="team-info">
                <div className="team-name">{m.name}</div>
                <div className="team-role">
                  {m.role || `${m.active_tasks} active`}
                </div>
              </div>
              <div className="load-bar">
                <div
                  className={`load-fill ${m.load_pct > 80 ? 'high' : ''}`}
                  style={{ width: `${m.load_pct}%` }}
                />
              </div>
              <span className="load-pct">{m.load_pct}%</span>
            </div>
          ))
        )}

        <div className="panel-rule" />

        <div className="section-label">
          <span>Activity</span>
          <span className="section-label-num">ii.</span>
        </div>
        {activity.length === 0 ? (
          <div className="placeholder-note">Nothing yet — mutations show up here.</div>
        ) : (
          activity.map((a) => (
            <div key={a.id} className="activity-item">
              <div className="activity-avatar">{a.actor_initials || '??'}</div>
              <div className="activity-text">
                <strong>{a.actor_name || 'Someone'}</strong>{' '}
                {activityVerbPhrase(a)}{' '}
                {a.task_code && <span className="mono-tag">{a.task_code}</span>}
                {a.verb === 'moved' && a.meta?.to && (
                  <> → {STATUS_LABEL[a.meta.to] || a.meta.to}</>
                )}
              </div>
              <span className="activity-time">{relativeTime(a.created_at)}</span>
            </div>
          ))
        )}
      </aside>

      <div className="corner-mark">Meridian · Folio · Phase 01</div>

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
      {newTaskStatus && (
        <NewTaskDialog
          initialStatus={newTaskStatus}
          onClose={() => setNewTaskStatus(null)}
          onCreate={handleCreateTask}
        />
      )}
    </div>
  )
}
