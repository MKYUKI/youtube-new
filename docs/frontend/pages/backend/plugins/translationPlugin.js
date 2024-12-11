// backend/plugins/translationPlugin.js
const axios = require('axios');

async function translateText(text, targetLang) {
  const apiKey = process.env.TRANSLATION_API_KEY;
  if (!apiKey) {
    // 翻訳APIキーがない場合はデモとしてそのままテキスト返す
    return text;
  }
  
  // ここでは架空の翻訳APIエンドポイントを利用
  // 実際にはDeepLやGoogle Translate APIを適宜利用する
  // 例: POST https://api.example.com/translate { text, targetLang }
  try {
    const response = await axios.post('https://api.example.com/translate', {
      text,
      targetLang
    }, {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });
    return response.data.translatedText;
  } catch (err) {
    console.error('Translation failed:', err.message);
    return text; // 失敗時は原文返す
  }
}

function applyPlugin(app) {
  // 単発翻訳エンドポイント
  app.post('/plugin/translation/translate', async (req, res) => {
    const { text, lang } = req.body;
    if (!text || !lang) {
      return res.status(400).json({ error: 'Missing text or lang parameter' });
    }
    try {
      const translated = await translateText(text, lang);
      res.json({ translated });
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'Translation error' });
    }
  });
}

module.exports = {
  applyPlugin,
  translateText
};
