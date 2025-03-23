// config-manager.js 
const fs = require('fs');
const path = require('path');

// Path to the config file 
const configPath = path.join(__dirname, 'config.json');

// Default configuration 
const defaultConfig = {
    fermiaIp: '',
    fermiaMac: '',
    wifiSsid: '',
    wifiPassword: '',
    username: 'arisenthil',
    password: '1012'
};


// Load configuration
function loadConfig() {
    try {
      if (fs.existsSync(configPath)) {
        const configData = fs.readFileSync(configPath, 'utf8');
        return JSON.parse(configData);
      }
    } catch (error) {
        console.error('Error loading config:', error);
    }
    
    // If file doesn't exist or there's an error, return default config
    return defaultConfig;
}

// Save configuration 

function saveConfig(config) {
    try {
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        return true;
    } catch (error) {
        console.error('Error saving config:', error);
        return false;
    }
}

module.exports = {
    loadConfig,
    saveConfig
};
