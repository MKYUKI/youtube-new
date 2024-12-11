// backend/plugins/index.js
const fs = require('fs');
const path = require('path');

function loadPlugins(app) {
  // 将来的に動的ロード可能。現在はsamplePluginだけ手動読み込み。
  const pluginPath = path.join(__dirname, 'samplePlugin.js');
  if (fs.existsSync(pluginPath)) {
    const plugin = require(pluginPath);
    if (typeof plugin.applyPlugin === 'function') {
      plugin.applyPlugin(app);
      console.log(`Loaded plugin: samplePlugin`);
    }
  }
}

module.exports = {
  loadPlugins
};

