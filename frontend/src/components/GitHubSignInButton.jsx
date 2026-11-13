const GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize';

export default function GitHubSignInButton({ isSubmitting }) {
  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID;
  const redirectUri = import.meta.env.VITE_GITHUB_REDIRECT_URI || `${window.location.origin}/`;

  function startSignIn() {
    const state = window.crypto.randomUUID();
    window.sessionStorage.setItem('github_oauth_state', state);
    const authorizeUrl = new URL(GITHUB_AUTH_URL);
    authorizeUrl.search = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      scope: 'read:user user:email',
      state,
    });
    window.location.assign(authorizeUrl);
  }

  if (!clientId) {
    return <p className="github-sign-in-note">Set VITE_GITHUB_CLIENT_ID to enable GitHub sign-in.</p>;
  }

  return (
    <button className="github-sign-in-button" type="button" disabled={isSubmitting} onClick={startSignIn}>
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <path fill="currentColor" d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.55.1.76-.24.76-.53v-2.08c-3.1.67-3.76-1.32-3.76-1.32-.5-1.29-1.24-1.63-1.24-1.63-1.01-.69.08-.68.08-.68 1.12.08 1.71 1.15 1.71 1.15 1 .1.76 2.26 3.45 1.59.1-.72.39-1.21.7-1.49-2.48-.28-5.09-1.24-5.09-5.53 0-1.22.44-2.22 1.15-3-.12-.28-.5-1.42.11-2.96 0 0 .94-.3 3.05 1.15a10.6 10.6 0 0 1 5.55 0c2.12-1.44 3.05-1.15 3.05-1.15.61 1.54.23 2.68.11 2.96.72.78 1.15 1.78 1.15 3 0 4.3-2.61 5.24-5.1 5.52.4.35.75 1.03.75 2.08V22c0 .3.2.64.77.53A11.1 11.1 0 0 0 12 .9Z" />
      </svg>
      Continue with GitHub
    </button>
  );
}
