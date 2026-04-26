import { useRef } from 'react'
import { MessageSquare, Paperclip, Pencil } from 'lucide-react'

const PRIORITY_STYLES = {
  high: { color: 'var(--accent)', label: 'High' },
  medium: { color: 'var(--ink-60)', label: 'Med' },
  low: { color: 'var(--ink-40)', label: 'Low' },
}

function formatDue(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

export default function TaskCard({ task, onDragStart, isDragging, onOpen, onEdit }) {
  const pri = PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium
  const downRef = useRef({ x: 0, y: 0 })
  const stop = (e) => e.stopPropagation()
  return (
    <div
      className="card"
      data-task-id={task.id}
      draggable
      onDragStart={(e) => onDragStart(e, task)}
      onMouseDown={(e) => {
        downRef.current = { x: e.clientX, y: e.clientY }
      }}
      onMouseUp={(e) => {
        const dx = Math.abs(e.clientX - downRef.current.x)
        const dy = Math.abs(e.clientY - downRef.current.y)
        if (dx < 4 && dy < 4 && onOpen) onOpen(task.id)
      }}
      style={{ opacity: isDragging ? 0.4 : 1, cursor: 'pointer' }}
    >
      <div className="card-top">
        <span className="card-id">{task.code}</span>
        <div className="card-top-right">
          <button
            type="button"
            className="card-edit-btn"
            aria-label="Edit task"
            onMouseDown={stop}
            onMouseUp={stop}
            onClick={(e) => {
              e.stopPropagation()
              onEdit?.(task.id)
            }}
            draggable={false}
            onDragStart={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
          >
            <Pencil size={14} strokeWidth={1.6} />
          </button>
          <span className="priority-dot" style={{ background: pri.color }} title={pri.label} />
        </div>
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
            <MessageSquare size={10} strokeWidth={1.5} /> {task.comment_count ?? 0}
          </span>
          <span>
            <Paperclip size={10} strokeWidth={1.5} /> {task.attachment_count ?? 0}
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
