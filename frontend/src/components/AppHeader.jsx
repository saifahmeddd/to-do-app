import { useDispatch, useSelector } from 'react-redux';
import { selectTheme, themeToggled } from '../features/ui/uiSlice.js';
import DatabaseIndicator from './DatabaseIndicator.jsx';

export default function AppHeader({ email, database, pendingCount, onLogout }) {
  const dispatch = useDispatch();
  const theme = useSelector(selectTheme);

  return (
    // Shows the signed-in user's summary and global theme/logout controls.
    <header className="app-header">
      <div>
        <div className="eyebrow">DDD + React</div>
        <h1>My tasks</h1>
        <p className="muted">
          Signed in as {email} · {pendingCount} pending
        </p>
        <DatabaseIndicator database={database} />
      </div>
      <div className="header-actions">
        <button className="secondary" onClick={() => dispatch(themeToggled())}>
          {theme === 'light' ? 'Dark mode' : 'Light mode'}
        </button>
        <button className="secondary" onClick={onLogout}>Log out</button>
      </div>
    </header>
  );
}
