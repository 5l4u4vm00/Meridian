# Folio — Remaining Work

Snapshot of the unfinished portion of the Folio project-management feature. Phases 1 and 2 have already shipped (see the completed list at the bottom). Only Phase 3 remains, plus a few small follow-ups deferred from earlier phases.

Source of truth for historical context: `~/.claude/plans/project-management-platform-jsx-look-th-snappy-storm.md`.

---

## Phase 3 — Comments + Attachments + Task Detail Drawer

### Goal

Let users open a task card, see its description, read/post comments, and attach files (metadata only — binary storage is a follow-up). Card footers should show real comment/attachment counts instead of the current hardcoded `0`s.

### Design decisions

- **Comments**: plain-text body for now; Markdown/mentions deferred.
- **Attachments**: metadata only (`filename`, `size_bytes`, `mime_type`, `url`, `uploaded_by_id`). The `POST` endpoint accepts the metadata and returns a placeholder `url`; no S3/local-disk upload in this phase.
- **Activity**: both comment and attachment writes emit an `ActivityEvent` via the existing writer in `task_service.py` / the new comment & attachment services.
- **UI**: open a right-side drawer when a card is clicked. Drawer shows title, description (editable), comment list, comment composer, attachment list, stub upload button. Escape / click-outside closes.
- **Counts on cards**: `TaskRead` schema grows `comment_count` + `attachment_count` computed in `TaskRead.from_task` (keeps `GET /projects/{code}/tasks` to a single query — load the counts eagerly or add two subqueries; for phase-3 scale, an N+1 with `len(task.comments)` behind a `selectin` relationship is fine).

### Backend — new files

Follow `routes → services → repositories → models`, same pattern as Phases 1/2.

- `Meridian_Server/app/models/comment.py` — `Comment(id, task_id FK CASCADE, author_id FK users, body Text, created_at)`. Register in `models/__init__.py`.
- `Meridian_Server/app/models/attachment.py` — `Attachment(id, task_id FK CASCADE, filename, size_bytes, mime_type, url, uploaded_by_id FK users, created_at)`. Register.
- `Meridian_Server/app/schemas/comment.py` — `CommentCreate`, `CommentRead` (with `author_initials`, `author_name`).
- `Meridian_Server/app/schemas/attachment.py` — `AttachmentCreateStub` (metadata only), `AttachmentRead` (with `uploader_initials`).
- `Meridian_Server/app/repositories/comment_repository.py` — `create`, `list_for_task`.
- `Meridian_Server/app/repositories/attachment_repository.py` — `create`, `list_for_task`.
- `Meridian_Server/app/services/comment_service.py` — `create_comment(db, task_id, body, actor_id)`; emits `activity_repository.create(..., verb="commented", meta={"preview": body[:80]})`.
- `Meridian_Server/app/services/attachment_service.py` — `create_attachment(db, task_id, payload, actor_id)`; emits `verb="attached"` with `meta={"filename": ...}`.
- `Meridian_Server/app/api/routes/comments.py` — `GET /tasks/{id}/comments`, `POST /tasks/{id}/comments`. Both behind `get_current_user`.
- `Meridian_Server/app/api/routes/attachments.py` — `GET /tasks/{id}/attachments`, `POST /tasks/{id}/attachments` (stub; return placeholder url like `/attachments/placeholder/{uuid}`).
- Mount both routers in `app/main.py` alongside existing ones.

### Backend — modifications

- `Meridian_Server/app/models/task.py` — add `comments = relationship("Comment", backref="task", cascade="all, delete-orphan", lazy="selectin")` and similarly for `attachments`.
- `Meridian_Server/app/schemas/task.py` — `TaskRead` gains `comment_count: int` and `attachment_count: int`; compute in `from_task(task)` as `len(task.comments or [])` / `len(task.attachments or [])`.
- `Meridian_Server/app/api/routes/tasks.py` — add `GET /tasks/{id}/detail` that returns the task plus comments and attachments in one payload (saves a round trip on drawer open). Alternatively let the client make three parallel calls; pick based on what feels simpler in `BoardPage.jsx`.

### Frontend — new files

- `Meridian_Client/src/api/comments.js` — `listComments(taskId)`, `createComment(taskId, body)`.
- `Meridian_Client/src/api/attachments.js` — `listAttachments(taskId)`, `createAttachment(taskId, metadata)`.
- `Meridian_Client/src/components/board/TaskDrawer.jsx` — new component. Props: `taskId`, `onClose`, `onChanged`. Fetches comments + attachments on mount; posts new ones; calls `onChanged` to let the parent refetch the board (so card counts update).
- `Meridian_Client/src/components/board/TaskCard.jsx` — finally extract the inline `TaskCard` function from `BoardPage.jsx` now that it grows an onClick for opening the drawer, plus real comment/attachment count rendering.

### Frontend — modifications

- `Meridian_Client/src/pages/BoardPage.jsx`:
  - Replace hardcoded `0` in card footer with `task.comment_count` and `task.attachment_count`.
  - Add state `detailTaskId`; clicking a card (but not the drag handle area) sets it; render `<TaskDrawer taskId={detailTaskId} onClose={...} onChanged={() => refreshBoard(activeCode)} />` when non-null.
  - Drawer open must not fire on drag end — track a `dragStartedAt` timestamp and suppress click if `<150ms` between dragstart and drop, or use a separate click target (e.g. the card title) rather than the whole card. Simpler: open drawer only when `mousedown` → `mouseup` happens with no drag.
- `Meridian_Client/src/pages/board.css` — add `.drawer-backdrop`, `.drawer`, `.drawer-head`, `.comment-list`, `.comment-item`, `.comment-composer`, `.attachment-row`.

### Tests

Backend:
- `Meridian_Server/tests/test_comments.py` — create, list (order by `created_at`), auth gate, emits activity (`verb=commented`), bumps `task.comment_count` visible on subsequent `GET /projects/{code}/tasks`.
- `Meridian_Server/tests/test_attachments.py` — stub create (returns placeholder url), list, auth gate, emits activity (`verb=attached`).

Frontend still has no harness (per `CLAUDE.md`); verify by clicking a card, posting a comment, confirming the card footer count increments and the Activity panel shows the new event.

### Verification (Phase 3)

1. `pytest` — all new and existing tests pass.
2. `npm run lint && npm run build` clean.
3. `docker compose up --build`; log in; open an existing task; drawer appears with empty comment list.
4. Post a comment → it renders in the drawer immediately, Activity panel adds a `commented` event, card footer count goes `0 → 1`.
5. Click "Add attachment" stub → attachment appears in drawer, Activity event added, paperclip count increments.

---

## Small follow-ups deferred from earlier phases

These are intentionally out of the phased PRs above but worth capturing so they don't get lost:

- **`ProjectSummary.progress %`** (Phase 1): `GET /projects` returns `task_count` only. Add a second field `progress_pct = shipped / total * 100` when total > 0. Touch: `Meridian_Server/app/schemas/project.py`, `app/api/routes/projects.py`, sidebar rendering in `BoardPage.jsx`.

- **Workload cap as a setting** (Phase 2): currently hardcoded `WORKLOAD_CAP = 10` in `Meridian_Server/app/services/stats_service.py`. Move to `app/core/config.py` (`workload_cap: int = 10`) so ops can tune it without a code change.

- **ACL enforcement** (Phase 1 design note): the `ProjectMember` table exists and every project creator is added as `lead`, but routes don't check membership — any authenticated user can mutate any project. Add a `require_project_member(code)` dep in `app/api/deps.py` and apply to project/task/comment/attachment routes. When this lands, update `tests/test_tasks.py::test_non_member_cannot_mutate` accordingly (currently a note in the plan, not a real test).

- **Split `BoardPage.jsx`**: the file has grown past ~800 lines with inline components. Once `TaskDrawer` and `TaskCard` are extracted in Phase 3, also lift `Sidebar`, `ProjectHeader`, `RightPanel`, `NewTaskDialog`, `NewProjectDialog` into `Meridian_Client/src/components/board/`. The original plan called this out; deferred because phase 1 was under the "single file is fine" threshold, but phase 3 tips it over.

- **Alembic migrations**: per `CLAUDE.md`, `Base.metadata.create_all` is "dev scaffolding — swap in Alembic before real data lands." Every model added in Phases 1–3 is still on `create_all`. Introduce Alembic, generate a baseline migration covering auth + projects + tasks + activity + comments + attachments, and wire `alembic upgrade head` into the docker-compose startup in place of `create_all`.

---

## What has already shipped (for quick recall)

### Phase 1 — Board MVP (shipped)

Backend: `models/{project,project_member,task}.py`, schemas, repositories with auto-numbering and fractional-index sort keys, services with `ProjectError`/`TaskError`, routes `GET/POST /projects`, `GET/PATCH /projects/{code}`, `GET/POST /projects/{code}/tasks`, `GET/PATCH /tasks/{id}`, `POST /tasks/{id}/move`. Tests: `test_projects.py`, `test_tasks.py`.

Frontend: `src/api/{projects,tasks}.js`, `src/pages/BoardPage.jsx` + `board.css` (sidebar, kanban, modals, cross-column HTML5 DnD, avatar menu with logout, empty-state onboarding). `App.jsx` routes `/` to `BoardPage` under `ProtectedRoute`. Vite proxy extended for `/projects` and `/tasks`. `lucide-react` installed. Old `HomePage.jsx` and root mockup deleted.

### Phase 2 — Stats + Workload + Activity + Intra-column reorder (shipped)

Backend: `models/activity_event.py`, `schemas/{activity,stats}.py`, `repositories/{activity,stats}_repository.py`, `services/{activity,stats}_service.py`, `task_service.py` rewritten to emit `created`/`updated`/`moved`/`completed` events. Routes `GET /projects/{code}/{stats,workload,activity}`. Tests: `test_activity.py`, `test_stats.py`, `test_workload.py`. **Total backend: 44/44 passing.**

Frontend: `src/api/activity.js`. `BoardPage.jsx` fetches stats/workload/activity alongside the board and refetches after mutations. Right panel renders real tiles (Open/Shipped/Overdue/Velocity), team-load bars (red above 80 %), activity feed with relative timestamps and `→` status transitions. Intra-column DnD computes `before_task_id` / `after_task_id` from sibling bounding rects and midpoint crossing. Lint clean, build clean.
