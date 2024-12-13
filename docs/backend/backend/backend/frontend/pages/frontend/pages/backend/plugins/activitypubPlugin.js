// backend/plugins/activitypubPlugin.js

const axios = require('axios');

async function fetchMastodonPublicTimeline() {
  // Mastodon public timeline API例 (最大3投稿取得)
  // この例では mastodon.socialを参照していますが、他のFediverseインスタンスにも適用可能
  // 本来はActivityPub ActorsやOutboxをフェッチするが、デモとしてMastodon APIを用いる
  const url = 'https://mastodon.social/api/v1/timelines/public?limit=3';
  const response = await axios.get(url);
  return response.data; // Mastodonの投稿オブジェクト配列
}

function applyPlugin(app) {
  app.get('/plugin/activitypub/content', async (req, res) => {
    try {
      const posts = await fetchMastodonPublicTimeline();
      // postsはMastodonステータスオブジェクトの配列
      // ここでは必要な部分のみ抜粋して返す
      const simplified = posts.map(p => ({
        type: 'activitypub',
        author: p.account?.display_name || p.account?.username,
        content: p.content,  // HTML
        createdAt: p.created_at
      }));
      res.json({ source: 'activitypubPlugin', data: simplified });
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'Failed to fetch ActivityPub data' });
    }
  });
}

module.exports = {
  applyPlugin
};
