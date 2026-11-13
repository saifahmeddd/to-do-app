import { useState } from 'react';

export default function TaskForm({ isSubmitting, onCreate }) {
  // Keep unfinished input local because no other component needs this draft value.
  const [title, setTitle] = useState('');
  const [submissionDate, setSubmissionDate] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanTitle = title.trim();

    if (!cleanTitle) return;

    // Wait for Redux to confirm success before clearing what the user typed.
    const created = await onCreate(cleanTitle, submissionDate || null);
    if (created) { setTitle(''); setSubmissionDate(''); }
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
      <label htmlFor="new-task-date">Submission date</label>
      <input id="new-task-date" type="date" value={submissionDate} onChange={event => setSubmissionDate(event.target.value)} disabled={isSubmitting} />
      <button className="primary" disabled={isSubmitting || !title.trim()}>
        {isSubmitting ? 'Adding…' : 'Add task'}
      </button>
    </form>
  );
}
