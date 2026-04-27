import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, ChevronUp, Plus, Search } from 'lucide-react'
import {
  createProject as apiCreateProject,
  listProjects as apiListProjects,
} from '../api/projects'
import NewProjectDialog from '../components/NewProjectDialog'
import { relativeTime } from '../utils/time'
import './board.css'
import './projects.css'

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'shipped', label: 'Shipped' },
  { key: 'empty', label: 'Empty' },
]

const DEFAULT_SORT_DIR = {
  name: 'asc',
  code: 'asc',
  tasks: 'desc',
  recent: 'desc',
}

function SortableHeader({ label, sortValue, sortKey, sortDir, onSort }) {
  const active = sortKey === sortValue
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onSort(sortValue)
    }
  }
  const ariaSort = active
    ? sortDir === 'asc'
      ? 'ascending'
      : 'descending'
    : 'none'
  return (
    <th
      className={`col-header sortable${active ? ' active' : ''}`}
      role="button"
      tabIndex={0}
      aria-sort={ariaSort}
      onClick={() => onSort(sortValue)}
      onKeyDown={handleKeyDown}
    >
      <span className="col-header-label">{label}</span>
      {active &&
        (sortDir === 'asc' ? (
          <ChevronUp size={12} strokeWidth={1.5} />
        ) : (
          <ChevronDown size={12} strokeWidth={1.5} />
        ))}
    </th>
  )
}

function compareProjects(a, b, key, dir) {
  let cmp
  switch (key) {
    case 'name':
      cmp = a.name.localeCompare(b.name)
      break
    case 'code':
      cmp = a.code.localeCompare(b.code)
      break
    case 'tasks':
      cmp = (a.task_count ?? 0) - (b.task_count ?? 0)
      break
    case 'recent':
    default: {
      const ta = a.last_activity ? new Date(a.last_activity).getTime() : 0
      const tb = b.last_activity ? new Date(b.last_activity).getTime() : 0
      cmp = ta - tb
    }
  }
  return dir === 'desc' ? -cmp : cmp
}

function matchesFilter(p, filter) {
  const total = p.task_count ?? 0
  const open = p.open_count ?? 0
  const shipped = p.shipped_count ?? 0
  if (filter === 'all') return true
  if (filter === 'empty') return total === 0
  if (filter === 'active') return open > 0
  if (filter === 'shipped') return total > 0 && shipped === total
  return true
}

export default function ProjectsPage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [sortKey, setSortKey] = useState('recent')
  const [sortDir, setSortDir] = useState(DEFAULT_SORT_DIR.recent)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showNewProject, setShowNewProject] = useState(false)

  useEffect(() => {
    let cancelled = false
      ; (async () => {
        try {
          setLoading(true)
          const list = await apiListProjects()
          if (!cancelled) setProjects(list)
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

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filtered = projects.filter((p) => {
      if (!matchesFilter(p, filter)) return false
      if (!q) return true
      return (
        p.name.toLowerCase().includes(q) || p.code.toLowerCase().includes(q)
      )
    })
    const sorted = [...filtered].sort((a, b) =>
      compareProjects(a, b, sortKey, sortDir),
    )
    return sorted
  }, [projects, query, filter, sortKey, sortDir])

  const activeCount = useMemo(
    () => projects.filter((p) => (p.open_count ?? 0) > 0).length,
    [projects],
  )

  const handleSort = (key) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(DEFAULT_SORT_DIR[key] ?? 'asc')
    }
  }

  const openProject = (code) => {
    navigate('/board', { state: { code } })
  }

  const handleCreate = async (payload) => {
    const created = await apiCreateProject(payload)
    setProjects((prev) => [
      {
        ...created,
        task_count: 0,
        open_count: 0,
        shipped_count: 0,
        last_activity: null,
      },
      ...prev,
    ])
  }

  const clearFilters = () => {
    setQuery('')
    setFilter('all')
  }

  return (
    <div className="projects-page">
      <header className="projects-brand">
        <div className="brand">
          <span className="brand-mark">Meridian</span>
        </div>
        <div className="brand-sub">A Project Studio</div>
        <div className="brand-rule" />
      </header>

      <section className="projects-title-row">
        <div>
          <h1 className="projects-title serif">Projects</h1>
          <div className="projects-meta">
            {loading
              ? 'Loading…'
              : `${projects.length} total · ${activeCount} active`}
          </div>
        </div>
        <button
          type="button"
          className="btn primary projects-new-btn"
          onClick={() => setShowNewProject(true)}
        >
          <Plus size={14} strokeWidth={1.5} />
          <span>New project</span>
        </button>
      </section>

      <section className="projects-toolbar">
        <div className="projects-search">
          <Search size={14} strokeWidth={1.5} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or code…"
          />
        </div>
        <div className="chip-row">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              className={`chip ${filter === f.key ? 'active' : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </section>

      {error && <div className="projects-error">{error}</div>}

      {!loading && !error && visible.length === 0 && (
        <div className="projects-empty">
          {projects.length === 0 ? (
            <>
              No projects yet.
              <button
                type="button"
                className="btn primary projects-empty-cta"
                onClick={() => setShowNewProject(true)}
              >
                Create your first project
              </button>
            </>
          ) : (
            <>
              No projects match these filters.
              <button
                type="button"
                className="btn projects-empty-cta"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            </>
          )}
        </div>
      )}

      {visible.length > 0 && (
        <table className="projects-table">
          <thead>
            <tr>
              <SortableHeader
                label="Code"
                sortValue="code"
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={handleSort}
              />
              <SortableHeader
                label="Name"
                sortValue="name"
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={handleSort}
              />
              <th className="col-header">Progress</th>
              <SortableHeader
                label="Tasks"
                sortValue="tasks"
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={handleSort}
              />
              <SortableHeader
                label="Last activity"
                sortValue="recent"
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={handleSort}
              />
            </tr>
          </thead>
          <tbody>
            {visible.map((p) => {
              const total = p.task_count ?? 0
              const shipped = p.shipped_count ?? 0
              const pct = total > 0 ? Math.round((shipped / total) * 100) : 0
              return (
                <tr
                  key={p.id}
                  className="project-row-tr"
                  onClick={() => openProject(p.code)}
                >
                  <td className="col-code">
                    <span
                      className="project-dot"
                      style={{ background: p.color }}
                    />
                    <span className="project-card-code">{p.code}</span>
                  </td>
                  <td className="col-name serif">{p.name}</td>
                  <td className="col-progress">
                    <div
                      className="progress"
                      role="progressbar"
                      aria-valuenow={pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
                      <div
                        className="progress-fill"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="progress-meta">
                      {shipped}/{total}
                    </div>
                  </td>
                  <td className="col-tasks">{total}</td>
                  <td className="col-activity">
                    {p.last_activity ? relativeTime(p.last_activity) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {showNewProject && (
        <NewProjectDialog
          onClose={() => setShowNewProject(false)}
          onCreate={handleCreate}
        />
      )}
    </div>
  )
}
