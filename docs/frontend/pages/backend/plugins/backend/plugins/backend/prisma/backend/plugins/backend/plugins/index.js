// backend/plugins/index.js
const fs = require('fs');
const path = require('path');

function loadPlugins(app) {
  const pluginFiles = [
    'samplePlugin.js',
    'activitypubPlugin.js',
    'translationPlugin.js',
    'oauthPlugin.js'
  ];
  
  pluginFiles.forEach(file => {
    const pluginPath = path.join(__dirname, file);
    if (fs.existsSync(pluginPath)) {
      const plugin = require(pluginPath);
      if (typeof plugin.applyPlugin === 'function') {
        plugin.applyPlugin(app);
        console.log(`Loaded plugin: ${file}`);
      }
    }
  });
}

module.exports = {
  loadPlugins
};
