import { useState } from 'react';
import DatabaseIndicator from './DatabaseIndicator.jsx';

export default function AuthForm({ mode, isSubmitting, error, activeDatabase, onSubmit, onModeChange }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const isRegistering = mode === 'register';

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({ email: email.trim(), password });
  }

  return (
    // Collects login or registration details and displays request feedback.
    <section className="auth-card" aria-labelledby="auth-title">
      <div className="eyebrow">React + Onion Architecture</div>
      <DatabaseIndicator database={activeDatabase} />
      <h1 id="auth-title">{isRegistering ? 'Create an account' : 'Welcome back'}</h1>
      <p className="muted">
        {isRegistering
          ? 'Create an account, then manage your own tasks.'
          : 'Log in to load the tasks owned by your account.'}
      </p>

      <form className="stack" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={event => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={event => setPassword(event.target.value)}
            autoComplete={isRegistering ? 'new-password' : 'current-password'}
            minLength={8}
            maxLength={128}
            required
          />
        </label>

        {error && <p className="message error" role="alert">{error}</p>}

        <button className="primary" disabled={isSubmitting}>
          {isSubmitting ? 'Please wait…' : isRegistering ? 'Register' : 'Log in'}
        </button>
      </form>

      <button
        className="text-button"
        type="button"
        onClick={() => onModeChange(isRegistering ? 'login' : 'register')}
      >
        {isRegistering
          ? 'Already registered? Log in'
          : 'Need an account? Register'}
      </button>
    </section>
  );
}
