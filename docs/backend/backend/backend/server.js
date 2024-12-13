// backend/server.js
const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { loadPlugins } = require('./plugins/index');

const {
  signupUser,
  loginUser,
  generateToken
} = require('./auth/auth');

const app = express();
const prisma = new PrismaClient();

app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend server running' });
});

// プラグインロード
loadPlugins(app);

// 認証API
app.post('/auth/signup', async (req, res) => {
  try {
    const { email, username, password } = req.body;
    const user = await signupUser({ email, username, password });
    const token = generateToken(user);
    res.json({ user: { id: user.id, email: user.email, username: user.username }, token });
  } catch (err) {
    console.error(err);
    res.status(400).json({ error: err.message });
  }
});

app.post('/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await loginUser({ email, password });
    const token = generateToken(user);
    res.json({ user: { id: user.id, email: user.email, username: user.username }, token });
  } catch (err) {
    console.error(err);
    res.status(401).json({ error: 'Invalid credentials' });
  }
});

// ユニバーサルフィードは前回定義済み
app.get('/universal-feed', async (req, res) => {
  try {
    const localTweets = await prisma.tweet.findMany({
      orderBy: { createdAt: 'desc' },
      take: 5,
      include: {
        author: {
          select: { username: true, displayName: true }
        }
      }
    });

    const pluginResponse = await fetch(`http://localhost:${process.env.PORT || 4000}/plugin/sample/content`)
      .then(r => r.json())
      .catch(() => ({ data: [] }));

    const externalData = pluginResponse.data || [];

    const unifiedFeed = [
      ...localTweets.map(t => ({
        type: 'local_tweet',
        content: t.content,
        author: t.author,
        createdAt: t.createdAt
      })),
      ...externalData.map(ed => ({
        type: 'external',
        title: ed.title,
        body: ed.body
      }))
    ];

    res.json({ feed: unifiedFeed });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch universal feed' });
  }
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Backend server listening on port ${PORT}`);
});
