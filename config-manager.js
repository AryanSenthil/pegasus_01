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
    password: '1012',
    jetsonIp: ''
};

// Load configuration
function loadConfig() {
    try {
      if (fs.existsSync(configPath)) {
        const configData = fs.readFileSync(configPath, 'utf8');
        try {
            return JSON.parse(configData);
        } catch (parseError) {
            console.error('Error parsing config JSON:', parseError);
            return defaultConfig;
        }
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
        // Make sure we have object with all required fields
        const completeConfig = {
            ...defaultConfig,
            ...config
        };
        
        fs.writeFileSync(configPath, JSON.stringify(completeConfig, null, 2));
        return true;
    } catch (error) {
        console.error('Error saving config:', error);
        return false;
    }
}

// Reset configuration to defaults
function resetConfig() {
    try {
        fs.writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
        return true;
    } catch (error) {
        console.error('Error resetting config:', error);
        return false;
    }
}

module.exports = {
    loadConfig,
    saveConfig,
    resetConfig
};