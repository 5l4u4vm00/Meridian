import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  LogOut,
  MoreHorizontal,
  Plus,
  Search,
  Trash2,
  Users,
} from 'lucide-react'
import TaskCard from '../components/board/TaskCard'
import TaskDrawer from '../components/board/TaskDrawer'
import EditTaskDialog from '../components/board/EditTaskDialog'
import Modal from '../components/Modal'
import NewProjectDialog from '../components/NewProjectDialog'
import Sidebar from '../components/Sidebar'
import { relativeTime } from '../utils/time'
import { useAuth } from '../auth/useAuth'
import {
  createProject as apiCreateProject,
  deleteProject as apiDeleteProject,
  listMembers as apiListMembers,
  listProjects as apiListProjects,
  updateProject as apiUpdateProject,
} from '../api/projects'
import {
  createTask as apiCreateTask,
  deleteTask as apiDeleteTask,
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
const PRIORITY_RANK = { high: 3, medium: 2, low: 1 }
function sortTasks(tasks, mode) {
  if (!mode) return tasks
  const copy = [...tasks]
  if (mode === 'priority') {
    copy.sort((a, b) => (PRIORITY_RANK[b.priority] ?? 0) - (PRIORITY_RANK[a.priority] ?? 0))
  } else if (mode === 'due') {
    copy.sort((a, b) => {
      if (!a.due_date && !b.due_date) return 0
      if (!a.due_date) return 1
      if (!b.due_date) return -1
      return a.due_date.localeCompare(b.due_date)
    })
  } else if (mode === 'title') {
    copy.sort((a, b) => (a.title || '').localeCompare(b.title || ''))
  }
  return copy
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
  if (title === 'Shipped') return <em>{title}</em>
  return title
}

const PRIORITY_DUE_OFFSET_DAYS = { high: 2, medium: 7, low: 14 }

function toDateInputValue(date) {
  const tzOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - tzOffset).toISOString().slice(0, 10)
}

function defaultDueDateFor(priority) {
  const d = new Date()
  d.setDate(d.getDate() + (PRIORITY_DUE_OFFSET_DAYS[priority] ?? 7))
  return toDateInputValue(d)
}

function NewTaskDialog({ initialStatus, onClose, onCreate }) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState('medium')
  const [tags, setTags] = useState('')
  const [status, setStatus] = useState(initialStatus)
  const [dueDate, setDueDate] = useState(() => defaultDueDateFor('medium'))
  const [dueDateTouched, setDueDateTouched] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const today = toDateInputValue(new Date())

  useEffect(() => {
    if (!dueDateTouched) setDueDate(defaultDueDateFor(priority))
  }, [priority, dueDateTouched])

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (dueDate && dueDate < today) {
      setError('Due date cannot be earlier than today')
      return
    }
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
        ...(dueDate ? { due_date: dueDate } : {}),
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
          <span className="field-label">Due date</span>
          <input
            type="date"
            value={dueDate}
            min={today}
            onClick={(e) => {
              if (typeof e.currentTarget.showPicker === 'function') {
                try {
                  e.currentTarget.showPicker()
                } catch {
                  // browser refused (e.g., not a user gesture) — ignore
                }
              }
            }}
            onChange={(e) => {
              setDueDateTouched(true)
              setDueDate(e.target.value)
            }}
          />
        </label>
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


function ChangeLeaderDialog({ projectCode, onClose, onSaved }) {
  const [members, setMembers] = useState([])
  const [leadId, setLeadId] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
      ; (async () => {
        try {
          const list = await apiListMembers(projectCode)
          if (cancelled) return
          setMembers(list)
          const current = list.find((m) => m.role === 'lead')
          if (current) setLeadId(String(current.id))
          else if (list[0]) setLeadId(String(list[0].id))
        } catch (e) {
          if (!cancelled) setError(e.message || 'Failed to load members')
        } finally {
          if (!cancelled) setLoading(false)
        }
      })()
    return () => {
      cancelled = true
    }
  }, [projectCode])

  const submit = async (e) => {
    e.preventDefault()
    if (!leadId) return
    setSubmitting(true)
    setError(null)
    try {
      await apiUpdateProject(projectCode, { lead_id: Number(leadId) })
      await onSaved()
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to update leader')
      setSubmitting(false)
    }
  }

  return (
    <Modal title="Change leader" onClose={onClose}>
      <form onSubmit={submit} className="modal-body">
        {loading ? (
          <div className="placeholder-note">Loading members…</div>
        ) : (
          <label className="field">
            <span className="field-label">Leader</span>
            <select value={leadId} onChange={(e) => setLeadId(e.target.value)}>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.email})
                </option>
              ))}
            </select>
          </label>
        )}
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={submitting || loading || !leadId}>
            Save
          </button>
        </div>
      </form>
    </Modal>
  )
}

function DeleteProjectDialog({ projectCode, projectName, onClose, onDeleted }) {
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const matches = confirm === projectCode

  const submit = async (e) => {
    e.preventDefault()
    if (!matches) return
    setSubmitting(true)
    setError(null)
    try {
      await apiDeleteProject(projectCode)
      await onDeleted()
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to delete project')
      setSubmitting(false)
    }
  }

  return (
    <Modal title="Delete project" onClose={onClose}>
      <form onSubmit={submit} className="modal-body">
        <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5 }}>
          This permanently removes <strong>{projectName}</strong> and all its tasks,
          comments, and attachments. This cannot be undone.
        </p>
        <label className="field">
          <span className="field-label">
            Type <span className="mono">{projectCode}</span> to confirm
          </span>
          <input
            autoFocus
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={projectCode}
          />
        </label>
        {error && <div className="form-error">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!matches || submitting}>
            Delete project
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function BoardPage() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

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
  const [detailTaskId, setDetailTaskId] = useState(null)
  const [editTaskId, setEditTaskId] = useState(null)
  const [search, setSearch] = useState('')
  const [columnSorts, setColumnSorts] = useState({})
  const [headerMenuOpen, setHeaderMenuOpen] = useState(false)
  const [showChangeLeader, setShowChangeLeader] = useState(false)
  const [showDeleteProject, setShowDeleteProject] = useState(false)

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
      ; (async () => {
        try {
          setLoading(true)
          const list = await apiListProjects()
          if (cancelled) return
          setProjects(list)
          const requestedCode = location.state?.code
          const initial =
            (requestedCode && list.find((p) => p.code === requestedCode)?.code) ||
            list[0]?.code ||
            null
          setActiveCode(initial)
          if (requestedCode) {
            navigate('/board', { replace: true, state: null })
          }
        } catch (e) {
          if (!cancelled) setError(e.message || 'Failed to load projects')
        } finally {
          if (!cancelled) setLoading(false)
        }
      })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!activeCode) return undefined
    let cancelled = false
      ; (async () => {
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

  const handleDeleteTask = async (id) => {
    try {
      await apiDeleteTask(id)
      await refreshBoard(activeCode)
      await refreshProjects()
    } catch (err) {
      setError(err.message || 'Failed to delete task')
    }
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
            <span className="brand-mark">Meridian</span>
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
  const q = search.trim().toLowerCase()
  const visibleColumns = q
    ? columns.map((c) => ({
      ...c,
      tasks: c.tasks.filter(
        (t) =>
          t.title?.toLowerCase().includes(q) ||
          t.code?.toLowerCase().includes(q) ||
          t.tags?.some((tag) => tag.toLowerCase().includes(q)),
      ),
    }))
    : columns

  return (
    <div className="pm-root">
      <Sidebar
        activeKey="project"
        projects={projects}
        activeProjectCode={activeCode}
        onSelectProject={(code) => setActiveCode(code)}
        onNewProject={() => setShowNewProject(true)}
      />

      <main className="main">
        <div className="topbar">
          <Link to="/" className="btn back-btn">
            <ArrowLeft size={13} strokeWidth={1.8} /> Projects
          </Link>
          <div style={{ flex: 1 }} />
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
            <button className="btn primary" onClick={() => setNewTaskStatus('backlog')}>
              <Plus size={13} strokeWidth={1.8} /> New task
            </button>
            <div className="user-menu">
              <button
                className="btn"
                onClick={() => setHeaderMenuOpen((v) => !v)}
                aria-label="Project actions"
              >
                <MoreHorizontal size={13} strokeWidth={1.5} />
              </button>
              {headerMenuOpen && (
                <div className="menu" onMouseLeave={() => setHeaderMenuOpen(false)}>
                  <button
                    className="menu-item"
                    onClick={() => {
                      setHeaderMenuOpen(false)
                      setShowChangeLeader(true)
                    }}
                  >
                    <Users size={13} strokeWidth={1.5} /> Change leader
                  </button>
                  <button
                    className="menu-item menu-item--danger"
                    onClick={() => {
                      setHeaderMenuOpen(false)
                      setShowDeleteProject(true)
                    }}
                  >
                    <Trash2 size={13} strokeWidth={1.5} /> Delete project
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="board-toolbar">
          <div className="search">
            <Search size={14} strokeWidth={1.5} color="var(--ink-60)" />
            <input
              placeholder="Search tasks"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="board">
          {visibleColumns.map((col) => {
            const sortedTasks = sortTasks(col.tasks, columnSorts[col.status])
            return (
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
                  <div className="column-head-meta">
                    <select
                      className="column-sort"
                      value={columnSorts[col.status] || ''}
                      onChange={(e) =>
                        setColumnSorts((prev) => ({
                          ...prev,
                          [col.status]: e.target.value || undefined,
                        }))
                      }
                      aria-label={`Sort ${STATUS_LABEL[col.status]}`}
                    >
                      <option value="">Sort</option>
                      <option value="priority">Priority</option>
                      <option value="due">Due date</option>
                      <option value="title">Title</option>
                    </select>
                    <span className="column-count">
                      {String(col.tasks.length).padStart(2, '0')}
                    </span>
                  </div>
                </div>

                {sortedTasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onDragStart={onDragStart}
                    isDragging={draggingId === task.id}
                    onOpen={(id) => setDetailTaskId(id)}
                    onEdit={(id) => setEditTaskId(id)}
                    onDelete={handleDeleteTask}
                  />
                ))}

                <button
                  className="add-card"
                  onClick={() => setNewTaskStatus(col.status)}
                >
                  + Add Task
                </button>
              </div>
            )
          })}
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
      {detailTaskId != null && (
        <TaskDrawer
          key={detailTaskId}
          taskId={detailTaskId}
          onClose={() => setDetailTaskId(null)}
          onChanged={() => refreshBoard(activeCode)}
        />
      )}
      {editTaskId != null && (
        <EditTaskDialog
          key={editTaskId}
          taskId={editTaskId}
          onClose={() => setEditTaskId(null)}
          onSave={async () => {
            await refreshBoard(activeCode)
            await refreshProjects()
          }}
        />
      )}
      {showChangeLeader && activeCode && (
        <ChangeLeaderDialog
          projectCode={activeCode}
          onClose={() => setShowChangeLeader(false)}
          onSaved={refreshProjects}
        />
      )}
      {showDeleteProject && activeProject && (
        <DeleteProjectDialog
          projectCode={activeProject.code}
          projectName={activeProject.name}
          onClose={() => setShowDeleteProject(false)}
          onDeleted={async () => {
            navigate('/')
          }}
        />
      )}
    </div>
  )
}
