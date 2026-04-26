import { useState } from 'react'
import Modal from './Modal'
import { DEFAULT_PROJECT_COLORS } from './projectColors'

export default function NewProjectDialog({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [color, setColor] = useState(DEFAULT_PROJECT_COLORS[0])
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
            {DEFAULT_PROJECT_COLORS.map((c) => (
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
