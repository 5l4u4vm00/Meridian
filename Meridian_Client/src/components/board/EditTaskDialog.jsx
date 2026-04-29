import { useEffect, useState } from 'react'
import Modal from '../Modal'
import { getTaskDetail as apiGetTaskDetail, updateTask as apiUpdateTask } from '../../api/tasks'

function toDateInputValue(date) {
  const tzOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - tzOffset).toISOString().slice(0, 10)
}

export default function EditTaskDialog({ taskId, onClose, onSave }) {
  const [loading, setLoading] = useState(true)
  const [original, setOriginal] = useState(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [dueDate, setDueDate] = useState('')
  const [tags, setTags] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const today = toDateInputValue(new Date())

  useEffect(() => {
    let cancelled = false
    apiGetTaskDetail(taskId)
      .then((detail) => {
        if (cancelled) return
        const t = detail.task
        setOriginal(t)
        setTitle(t.title || '')
        setDescription(t.description || '')
        setPriority(t.priority || 'medium')
        setDueDate(t.due_date ? t.due_date.slice(0, 10) : '')
        setTags((t.tags || []).join(', '))
        setLoading(false)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e.message || 'Failed to load task')
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [taskId])

  const submit = async (e) => {
    e.preventDefault()
    if (!original) return
    setError(null)
    if (dueDate && dueDate < today && dueDate !== (original.due_date || '').slice(0, 10)) {
      setError('Due date cannot be earlier than today')
      return
    }

    const payload = {}
    const trimmedTitle = title.trim()
    if (trimmedTitle !== original.title) payload.title = trimmedTitle
    if (description !== (original.description || '')) payload.description = description
    if (priority !== original.priority) payload.priority = priority
    const origDue = original.due_date ? original.due_date.slice(0, 10) : ''
    if (dueDate !== origDue) payload.due_date = dueDate || null
    const nextTags = tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)
    const origTags = original.tags || []
    const tagsChanged =
      nextTags.length !== origTags.length ||
      nextTags.some((t, i) => t !== origTags[i])
    if (tagsChanged) payload.tags = nextTags

    if (Object.keys(payload).length === 0) {
      onClose()
      return
    }

    setSubmitting(true)
    try {
      await apiUpdateTask(taskId, payload)
      await onSave?.()
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to update task')
      setSubmitting(false)
    }
  }

  return (
    <Modal title="Edit task" onClose={onClose}>
      {loading ? (
        <div className="modal-body" style={{ color: 'var(--ink-60)' }}>Loading…</div>
      ) : (
        <form onSubmit={submit} className="modal-body">
          <label className="field">
            <span className="field-label">Title</span>
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </label>
          <label className="field">
            <span className="field-label">Description</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
            />
          </label>
          <div className="field-row">
            <label className="field">
              <span className="field-label">Priority</span>
              <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </label>
            <label className="field">
              <span className="field-label">Due date</span>
              <input
                type="date"
                value={dueDate}
                onClick={(e) => {
                  if (typeof e.currentTarget.showPicker === 'function') {
                    try {
                      e.currentTarget.showPicker()
                    } catch {
                      // browser refused — ignore
                    }
                  }
                }}
                onChange={(e) => setDueDate(e.target.value)}
              />
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
              {submitting ? 'Saving…' : 'Update task'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  )
}
