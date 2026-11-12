import { useEffect, useRef, useState } from 'react';

let googleScript;

function loadGoogleIdentity() {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (!googleScript) {
    googleScript = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
  return googleScript;
}

export default function GoogleSignInButton({ onCredential }) {
  const buttonRef = useRef(null);
  const credentialHandler = useRef(onCredential);
  const [loadError, setLoadError] = useState('');
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    credentialHandler.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    if (!clientId) return undefined;
    let active = true;
    const buttonElement = buttonRef.current;

    loadGoogleIdentity()
      .then(() => {
        if (!active || !buttonElement) return;
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: response => {
            if (response.credential) credentialHandler.current(response.credential);
          },
        });
        window.google.accounts.id.renderButton(buttonElement, {
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          width: 360,
        });
      })
      .catch(() => {
        if (active) setLoadError('Google sign-in could not load. Check your connection.');
      });

    return () => {
      active = false;
      if (buttonElement) buttonElement.innerHTML = '';
    };
  }, [clientId]);

  if (!clientId) {
    return <p className="google-sign-in-note">Set VITE_GOOGLE_CLIENT_ID to enable Google sign-in.</p>;
  }

  return (
    <div className="google-sign-in">
      <div ref={buttonRef} />
      {loadError && <p className="message error" role="alert">{loadError}</p>}
    </div>
  );
}
