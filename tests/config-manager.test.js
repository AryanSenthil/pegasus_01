const fs = require('fs');
const path = require('path');
const { loadConfig, saveConfig } = require('../config-manager');

// Mock fs module
jest.mock('fs');

describe('Config Manager', () => {
    const testConfig = {
        fermiaIp: '192.168.1.1',
        fermiaMac: '00:11:22:33:44:55',
        wifiSsid: 'TestWifi',
        wifiPassword: 'testpass',
        username: 'testuser',
        password: 'testpass'
    };

    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
    });

    describe('loadConfig', () => {
        it('should load existing config file', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockReturnValue(JSON.stringify(testConfig));

            const config = loadConfig();
            expect(config).toEqual(testConfig);
            expect(fs.existsSync).toHaveBeenCalled();
            expect(fs.readFileSync).toHaveBeenCalled();
        });

        it('should return default config when file does not exist', () => {
            fs.existsSync.mockReturnValue(false);

            const config = loadConfig();
            expect(config).toHaveProperty('username', 'arisenthil');
            expect(config).toHaveProperty('password', '1012');
            expect(fs.existsSync).toHaveBeenCalled();
            expect(fs.readFileSync).not.toHaveBeenCalled();
        });

        it('should return default config on error', () => {
            fs.existsSync.mockReturnValue(true);
            fs.readFileSync.mockImplementation(() => {
                throw new Error('Read error');
            });

            const config = loadConfig();
            expect(config).toHaveProperty('username', 'arisenthil');
            expect(config).toHaveProperty('password', '1012');
        });
    });

    describe('saveConfig', () => {
        it('should save config successfully', () => {
            fs.writeFileSync.mockImplementation(() => {});

            const result = saveConfig(testConfig);
            expect(result).toBe(true);
            expect(fs.writeFileSync).toHaveBeenCalledWith(
                expect.any(String),
                JSON.stringify(testConfig, null, 2)
            );
        });

        it('should return false on save error', () => {
            fs.writeFileSync.mockImplementation(() => {
                throw new Error('Write error');
            });

            const result = saveConfig(testConfig);
            expect(result).toBe(false);
        });
    });
});
