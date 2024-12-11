// frontend/pages/login.js
import React, { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:4000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.token) {
        localStorage.setItem('authToken', data.token);
        setMessage('Login successful! Token stored.');
      } else {
        setMessage('Login failed: ' + data.error);
      }
    } catch (err) {
      console.error(err);
      setMessage('Error logging in');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Log In</h1>
      <form onSubmit={handleLogin}>
        <div>
          <label>Email:</label><br/>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required/>
        </div>
        <div>
          <label>Password:</label><br/>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required/>
        </div>
        <button type="submit">Log In</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}
