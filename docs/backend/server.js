// backend/server.js
const express = require('express');
const app = express();

// Basic middleware setup
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend server running' });
});

// TODO: Future routes for auth, tweets, etc. will be added

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Backend server listening on port ${PORT}`);
});
