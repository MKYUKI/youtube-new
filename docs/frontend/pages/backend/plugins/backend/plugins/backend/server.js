// backend/server.js
const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { loadPlugins } = require('./plugins/index');
const fetch = require('node-fetch'); 
const {
  signupUser,
  loginUser,
  generateToken
} = require('./auth/auth');

const { translateText } = require('./plugins/translationPlugin');

const app = express();
const prisma = new PrismaClient();

app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend server running' });
});

// WebFingerエンドポイント
app.get('/.well-known/webfinger', (req, res) => {
  const resource = req.query.resource;
  if (resource) {
    res.json({
      subject: resource,
      links: [
        {
          rel: 'self',
          type: 'application/activity+json',
          href: `http://localhost:${process.env.PORT || 4000}/users/someuser`
        }
      ]
    });
  } else {
    res.status(400).json({ error: 'No resource provided' });
  }
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

// ユニバーサルフィード
app.get('/universal-feed', async (req, res) => {
  try {
    const targetLang = req.query.lang; // 例: ?lang=ja で日本語翻訳要求
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

    const activitypubResponse = await fetch(`http://localhost:${process.env.PORT || 4000}/plugin/activitypub/content`)
      .then(r => r.json())
      .catch(() => ({ data: [] }));
    const activitypubData = activitypubResponse.data || [];

    let unifiedFeed = [
      ...localTweets.map(t => ({
        type: 'local_tweet',
        content: t.content,
        author: t.author.displayName || t.author.username,
        createdAt: t.createdAt
      })),
      ...externalData.map(ed => ({
        type: 'external',
        title: ed.title,
        body: ed.body,
        createdAt: new Date().toISOString(),
        author: 'External Source'
      })),
      ...activitypubData
    ];

    // 翻訳要求がある場合、全てのテキストを翻訳する
    if (targetLang) {
      unifiedFeed = await Promise.all(unifiedFeed.map(async item => {
        // 翻訳対象フィールド: content, title, body, author等
        if (item.content) {
          item.content = await translateText(item.content, targetLang);
        }
        if (item.title) {
          item.title = await translateText(item.title, targetLang);
        }
        if (item.body) {
          item.body = await translateText(item.body, targetLang);
        }
        if (item.author) {
          item.author = await translateText(item.author, targetLang);
        }
        return item;
      }));
    }

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
