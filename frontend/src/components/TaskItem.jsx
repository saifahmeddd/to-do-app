import { useState } from 'react';

export default function TaskItem({ task, isBusy, onComplete, onRename, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(task.title);

  const isCompleted = Boolean(task.completed_at);

  async function handleRename(event) {
    event.preventDefault();
    const cleanTitle = draftTitle.trim();

    if (!cleanTitle || cleanTitle === task.title) {
      setDraftTitle(task.title);
      setIsEditing(false);
      return;
    }

    const renamed = await onRename(task.id, cleanTitle);
    if (renamed) setIsEditing(false);
  }

  function cancelEditing() {
    setDraftTitle(task.title);
    setIsEditing(false);
  }

  return (
    // Shows one task, switching between its details and edit form.
    <li className={`task-item ${isCompleted ? 'completed' : ''}`}>
      <div className="task-content">
        <span className="status-dot" aria-hidden="true" />

        {isEditing ? (
          <form className="edit-form" onSubmit={handleRename}>
            <label className="sr-only" htmlFor={`edit-${task.id}`}>Edit title</label>
            <input
              id={`edit-${task.id}`}
              value={draftTitle}
              onChange={event => setDraftTitle(event.target.value)}
              maxLength={120}
              autoFocus
              disabled={isBusy}
            />
            <button className="small" disabled={isBusy || !draftTitle.trim()}>Save</button>
            <button className="small secondary" type="button" onClick={cancelEditing}>
              Cancel
            </button>
          </form>
        ) : (
          <div>
            <p className="task-title">{task.title}</p>
            <p className="task-date">
              Created {new Date(task.created_at).toLocaleString()}
            </p>
            {task.submission_date && <p className="task-date">Due {new Date(`${task.submission_date}T00:00:00`).toLocaleDateString()}</p>}
          </div>
        )}
      </div>

      {!isEditing && (
        <div className="task-actions">
          {!isCompleted && (
            <button className="small" disabled={isBusy} onClick={() => onComplete(task.id)}>
              Complete
            </button>
          )}
          <button className="small secondary" disabled={isBusy} onClick={() => setIsEditing(true)}>
            Edit
          </button>
          <button className="small danger" disabled={isBusy} onClick={() => onDelete(task.id)}>
            Delete
          </button>
        </div>
      )}
    </li>
  );
}
