import { useState } from 'react';

export default function TaskForm({ isSubmitting, onCreate }) {
  // Keep unfinished input local because no other component needs this draft value.
  const [title, setTitle] = useState('');
  const [submissionAt, setSubmissionAt] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanTitle = title.trim();

    if (!cleanTitle) return;

    // Wait for Redux to confirm success before clearing what the user typed.
    const created = await onCreate(cleanTitle, submissionAt ? new Date(submissionAt).toISOString() : null);
    if (created) { setTitle(''); setSubmissionAt(''); }
  }

  return (
    // Collects a new task title and shows whether creation is in progress.
    <form className="task-form" onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="new-task-title">New task title</label>
      <input
        id="new-task-title"
        value={title}
        onChange={event => setTitle(event.target.value)}
        placeholder="What needs to be done?"
        maxLength={120}
        disabled={isSubmitting}
      />
      <label htmlFor="new-task-date">Due date and time (optional)</label>
      <input id="new-task-date" type="datetime-local" value={submissionAt} onChange={event => setSubmissionAt(event.target.value)} disabled={isSubmitting} />
      <small>We’ll email you when it’s due. Schedule within the next 30 days.</small>
      <button className="primary" disabled={isSubmitting || !title.trim()}>
        {isSubmitting ? 'Adding…' : 'Add task'}
      </button>
    </form>
  );
}
