import { Link, useNavigate } from 'react-router-dom'
import {
  Archive,
  Calendar,
  Inbox,
  Layers,
  Plus,
  Settings,
  TrendingUp,
  Users,
} from 'lucide-react'

const WORKSPACE_ITEMS = [
  { key: 'inbox', icon: Inbox, label: 'Inbox', to: null },
  { key: 'my-tasks', icon: Layers, label: 'My Tasks', to: '/my-tasks' },
  { key: 'calendar', icon: Calendar, label: 'Calendar', to: null },
  { key: 'insights', icon: TrendingUp, label: 'Insights', to: null },
]

export default function Sidebar({
  activeKey,
  projects,
  activeProjectCode,
  onSelectProject,
  onNewProject,
}) {
  const navigate = useNavigate()
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">Meridian</span>
      </div>
      <div className="brand-sub">A Project Studio</div>
      <div className="brand-rule" />

      <div className="sidebar-section">
        <div className="section-label">
          <span>Workspace</span>
          <span className="section-label-num">i.</span>
        </div>
        {WORKSPACE_ITEMS.map((item) => {
          const isActive = activeKey === item.key
          const className = `nav-item${isActive ? ' active' : ''}`
          if (item.to) {
            return (
              <Link key={item.key} to={item.to} className={className}>
                <item.icon size={14} strokeWidth={1.5} />
                <span>{item.label}</span>
              </Link>
            )
          }
          return (
            <div key={item.key} className={className}>
              <item.icon size={14} strokeWidth={1.5} />
              <span>{item.label}</span>
            </div>
          )
        })}
      </div>

      <div className="sidebar-section">
        <div className="section-label">
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <span>Projects</span>
            <Link to="/" className="section-label-link">All</Link>
          </span>
          <span className="section-label-num">ii.</span>
        </div>
        {projects.map((p) => {
          const active =
            activeKey === 'project' && activeProjectCode === p.code
          const handleClick = () => {
            if (onSelectProject) onSelectProject(p.code)
            else navigate('/board', { state: { code: p.code } })
          }
          return (
            <div
              key={p.id}
              className={`project-row ${active ? 'active' : ''}`}
              onClick={handleClick}
            >
              <div className="project-dot" style={{ background: p.color }} />
              <span className="project-name">{p.name}</span>
              <span className="project-code">{p.code}</span>
            </div>
          )
        })}
        <div
          className="nav-item"
          style={{ color: 'var(--ink-40)', marginTop: 4, cursor: 'pointer' }}
          onClick={onNewProject}
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
  )
}
