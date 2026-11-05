import TaskItem from './TaskItem.jsx';

export default function TaskList({ tasks, busyTaskId, onComplete, onRename, onDelete }) {
  if (tasks.length === 0) {
    return (
      // Gives the user guidance when there are no tasks to display.
      <div className="empty-state">
        <h2>No tasks yet</h2>
        <p>Add your first task using the form above.</p>
      </div>
    );
  }

  // Stable task IDs let React preserve each TaskItem across list re-renders.
  return (
    // Renders each task with the callbacks and busy state it needs.
    <ul className="task-list">
      {tasks.map(task => (
        <TaskItem
          key={task.id}
          task={task}
          isBusy={busyTaskId === task.id}
          onComplete={onComplete}
          onRename={onRename}
          onDelete={onDelete}
        />
      ))}
    </ul>
  );
}
