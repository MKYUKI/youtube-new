// backend/server.js
const express = require('express');
const { PrismaClient } = require('@prisma/client');
const { loadPlugins } = require('./plugins/index');

const app = express();
const prisma = new PrismaClient();

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend server running' });
});

// プラグインロード
loadPlugins(app);

// ユニバーサルフィードエンドポイント
// 現状はローカルのツイート + samplePluginのコンテンツを統合して返す簡易例
app.get('/universal-feed', async (req, res) => {
  try {
    // ローカルの最新ツイート数件取得(仮に5件)
    const localTweets = await prisma.tweet.findMany({
      orderBy: { createdAt: 'desc' },
      take: 5,
      include: {
        author: {
          select: { username: true, displayName: true }
        }
      }
    });

    // samplePluginのコンテンツ取得(内部呼び出し)
    // 本来はプラグインごとにPromise.all()でまとめる設計を検討
    const pluginResponse = await fetch(`http://localhost:${process.env.PORT || 4000}/plugin/sample/content`).then(r => r.json()).catch(() => ({data:[]}));
    const externalData = pluginResponse.data || [];

    // ローカルコンテンツと外部コンテンツを統合
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
