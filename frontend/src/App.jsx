import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  authenticate,
  authenticateWithGoogle,
  loggedOut,
  modeChanged,
  selectAuthError,
  selectAuthMode,
  selectIsAuthenticating,
  selectSession,
} from './features/auth/authSlice.js';
import {
  completeTask,
  createTask,
  deleteTask,
  loadTasks,
  renameTask,
  selectBusyTaskId,
  selectIsCreating,
  selectIsLoadingTasks,
  selectPendingCount,
  selectTaskError,
  selectTasks,
  tasksCleared,
} from './features/tasks/tasksSlice.js';
import {
  loadActiveDatabase,
  selectActiveDatabase,
  selectTheme,
} from './features/ui/uiSlice.js';
import AppHeader from './components/AppHeader.jsx';
import AuthForm from './components/AuthForm.jsx';
import TaskForm from './components/TaskForm.jsx';
import TaskList from './components/TaskList.jsx';

export default function App() {
  // redux's dispatch function to dispatch actions to the store
  const dispatch = useDispatch();

  // subscription for all the required state values from the store
  const authMode = useSelector(selectAuthMode);
  const session = useSelector(selectSession);
  const isAuthenticating = useSelector(selectIsAuthenticating);
  const authError = useSelector(selectAuthError);
  const tasks = useSelector(selectTasks);
  const isLoadingTasks = useSelector(selectIsLoadingTasks);
  const isCreating = useSelector(selectIsCreating);
  const busyTaskId = useSelector(selectBusyTaskId);
  const taskError = useSelector(selectTaskError);
  const pendingCount = useSelector(selectPendingCount);
  const theme = useSelector(selectTheme);
  const activeDatabase = useSelector(selectActiveDatabase);

  // javascript's optional chaining
  const accessToken = session?.access_token;

  useEffect(() => {
    dispatch(loadActiveDatabase());
  }, [dispatch]);

  // side effect to set the theme on the document element
  useEffect(() => {
    document.documentElement.dataset.theme = theme;

    return () => {
      delete document.documentElement.dataset.theme;
    };
  }, [theme]);

  // Reload tasks for a new session and cancel the request during effect cleanup.
  useEffect(() => {
    if (!accessToken) return;

    const request = dispatch(loadTasks());

    return () => request.abort();
  }, [dispatch, accessToken]);

  const handleAuthentication = credentials => dispatch(authenticate(credentials));
  const handleGoogleAuthentication = idToken => dispatch(authenticateWithGoogle(idToken));
  const handleModeChange = mode => dispatch(modeChanged(mode));

  function handleLogout() {
    dispatch(loggedOut());
    dispatch(tasksCleared());
  }

  // unwrap turns the dispatched thunk result into normal Promise success or failure.
  async function runTaskAction(action) {
    try {
      await dispatch(action).unwrap();
      return true;
    } catch {
      return false;
    }
  }

  const handleCreate = title => runTaskAction(createTask(title));
  const handleComplete = id => runTaskAction(completeTask(id));
  const handleRename = (id, title) => runTaskAction(renameTask({ id, title }));
  const handleDelete = id => runTaskAction(deleteTask(id));

  if (!session) {
    return (
      <main className="auth-layout">
        <AuthForm
          mode={authMode}
          isSubmitting={isAuthenticating}
          error={authError}
          activeDatabase={activeDatabase}
          onSubmit={handleAuthentication}
          onGoogleSignIn={handleGoogleAuthentication}
          onModeChange={handleModeChange}
        />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <AppHeader
        email={session.email}
        database={session.database || activeDatabase}
        pendingCount={pendingCount}
        onLogout={handleLogout}
      />

      <section className="task-panel" aria-labelledby="task-panel-title">
        <h2 id="task-panel-title" className="sr-only">Task manager</h2>

        <TaskForm isSubmitting={isCreating} onCreate={handleCreate} />

        {taskError && <p className="message error" role="alert">{taskError}</p>}

        {isLoadingTasks ? (
          <p className="loading">Loading tasks…</p>
        ) : (
          <TaskList
            tasks={tasks}
            busyTaskId={busyTaskId}
            onComplete={handleComplete}
            onRename={handleRename}
            onDelete={handleDelete}
          />
        )}
      </section>
    </main>
  );
}
