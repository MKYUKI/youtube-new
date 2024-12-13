// frontend/pages/signup.js
import React, { useState } from 'react';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:4000/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, username, password })
      });
      const data = await res.json();
      if (data.token) {
        localStorage.setItem('authToken', data.token);
        setMessage('Signup successful! Token stored.');
      } else {
        setMessage('Signup failed: ' + data.error);
      }
    } catch (err) {
      console.error(err);
      setMessage('Error signing up');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Sign Up</h1>
      <form onSubmit={handleSignup}>
        <div>
          <label>Email:</label><br/>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required/>
        </div>
        <div>
          <label>Username:</label><br/>
          <input type="text" value={username} onChange={e => setUsername(e.target.value)} required/>
        </div>
        <div>
          <label>Password:</label><br/>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} required/>
        </div>
        <button type="submit">Sign Up</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  );
}
