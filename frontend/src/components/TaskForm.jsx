import { useState } from 'react';

export default function TaskForm({ isSubmitting, onCreate }) {
  // Keep unfinished input local because no other component needs this draft value.
  const [title, setTitle] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const cleanTitle = title.trim();

    if (!cleanTitle) return;

    // Wait for Redux to confirm success before clearing what the user typed.
    const created = await onCreate(cleanTitle);
    if (created) setTitle('');
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
      <button className="primary" disabled={isSubmitting || !title.trim()}>
        {isSubmitting ? 'Adding…' : 'Add task'}
      </button>
    </form>
  );
}
