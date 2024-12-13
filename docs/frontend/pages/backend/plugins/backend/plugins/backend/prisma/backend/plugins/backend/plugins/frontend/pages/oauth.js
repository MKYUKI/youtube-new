// frontend/pages/oauth.js
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function OAuthPage() {
  const router = useRouter();
  const [message, setMessage] = useState('');

  useEffect(() => {
    const { token } = router.query;
    if (token) {
      localStorage.setItem('authToken', token);
      setMessage('OAuth login successful! Token stored.');
    }
  }, [router.query]);

  return (
    <div style={{ padding: '20px' }}>
      <h1>OAuth Login</h1>
      <p>You can login using external providers:</p>
      <ul>
        <li><a href="http://localhost:4000/auth/oauth/google">Login with Google</a></li>
        <li><a href="http://localhost:4000/auth/oauth/github">Login with GitHub</a></li>
      </ul>
      {message && <p>{message}</p>}
    </div>
  );
}
