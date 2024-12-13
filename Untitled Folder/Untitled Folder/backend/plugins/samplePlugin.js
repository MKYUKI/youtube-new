// backend/plugins/samplePlugin.js

const axios = require('axios');

async function fetchExternalData() {
  // 仮の外部API呼び出し(本来はActivityPub等)
  // ここではダミーJSON Placeholder APIをサンプル利用
  const response = await axios.get('https://jsonplaceholder.typicode.com/posts?_limit=5');
  return response.data;
}

function applyPlugin(app) {
  app.get('/plugin/sample/content', async (req, res) => {
    try {
      const data = await fetchExternalData();
      res.json({ source: 'samplePlugin', data });
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'Failed to fetch external data' });
    }
  });
}

module.exports = {
  applyPlugin
};
