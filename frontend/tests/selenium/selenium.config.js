// ================================================================
// SELENIUM CONFIGURATION FOR E2E TESTING
// Tony WhatsApp Assistant - Frontend E2E Testing
// ================================================================

const { Builder } = require('selenium-webdriver');
const firefox = require('selenium-webdriver/firefox');

// Configuration constants
const SELENIUM_CONFIG = {
  // Base URL for testing
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:3000',
  
  // Browser configurations - Firefox only
  browsers: {
    firefox: {
      name: 'firefox',
      options: [
        '--headless',
        '--width=1920',
        '--height=1080',
        '--no-sandbox',
        '--disable-dev-shm-usage'
      ]
    }
  },
  
  // Test timeouts
  timeouts: {
    implicit: 10000,      // 10 seconds
    pageLoad: 30000,      // 30 seconds
    script: 30000,        // 30 seconds
    element: 15000        // 15 seconds
  },
  
  // Retry configuration
  retry: {
    attempts: 3,
    delay: 2000
  },
  
  // Screenshot configuration
  screenshots: {
    enabled: true,
    path: 'tests/screenshots',
    onFailure: true,
    onSuccess: false
  },
  
  // Video recording
  video: {
    enabled: false,
    path: 'tests/videos'
  },
  
  // Performance testing
  performance: {
    enabled: true,
    thresholds: {
      loadTime: 5000,       // 5 seconds
      firstContentfulPaint: 2000,  // 2 seconds
      largestContentfulPaint: 4000  // 4 seconds
    }
  },
  
  // Accessibility testing
  accessibility: {
    enabled: true,
    standards: ['WCAG2A', 'WCAG2AA']
  },
  
  // Mobile testing
  mobile: {
    enabled: true,
    devices: [
      {
        name: 'iPhone 12',
        width: 390,
        height: 844,
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
      },
      {
        name: 'Samsung Galaxy S21',
        width: 360,
        height: 800,
        userAgent: 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36'
      }
    ]
  }
};

// Driver factory - Firefox only
class DriverFactory {
  static async createDriver(browserName = 'firefox', headless = true) {
    const browser = SELENIUM_CONFIG.browsers[browserName];
    if (!browser) {
      throw new Error(`Unsupported browser: ${browserName}. Only Firefox is supported.`);
    }
    
    let driver;
    
    // Only Firefox is supported
    if (browserName === 'firefox') {
      const firefoxOptions = new firefox.Options();
      if (headless) {
        browser.options.forEach(option => firefoxOptions.addArguments(option));
      } else {
        // Remove headless option for debugging
        browser.options
          .filter(option => option !== '--headless')
          .forEach(option => firefoxOptions.addArguments(option));
      }
      
      driver = await new Builder()
        .forBrowser('firefox')
        .setFirefoxOptions(firefoxOptions)
        .build();
    } else {
      throw new Error(`Browser setup not implemented: ${browserName}. Only Firefox is supported.`);
    }
    
    // Set timeouts
    await driver.manage().setTimeouts({
      implicit: SELENIUM_CONFIG.timeouts.implicit,
      pageLoad: SELENIUM_CONFIG.timeouts.pageLoad,
      script: SELENIUM_CONFIG.timeouts.script
    });
    
    return driver;
  }
  
  static async createMobileDriver(deviceName = 'iPhone 12') {
    const device = SELENIUM_CONFIG.mobile.devices.find(d => d.name === deviceName);
    if (!device) {
      throw new Error(`Unsupported device: ${deviceName}`);
    }
    
    const firefoxOptions = new firefox.Options();
    firefoxOptions.addArguments('--headless');
    firefoxOptions.addArguments('--no-sandbox');
    firefoxOptions.addArguments('--disable-dev-shm-usage');
    firefoxOptions.addArguments(`--width=${device.width}`);
    firefoxOptions.addArguments(`--height=${device.height}`);
    firefoxOptions.setPreference('general.useragent.override', device.userAgent);
    
    const driver = await new Builder()
      .forBrowser('firefox')
      .setFirefoxOptions(firefoxOptions)
      .build();
    
    return driver;
  }
}

// Test utilities
class TestUtils {
  static async takeScreenshot(driver, filename) {
    if (!SELENIUM_CONFIG.screenshots.enabled) return;
    
    const fs = require('fs');
    const path = require('path');
    
    const screenshotPath = path.join(SELENIUM_CONFIG.screenshots.path, filename);
    const screenshot = await driver.takeScreenshot();
    
    // Ensure directory exists
    const dir = path.dirname(screenshotPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    fs.writeFileSync(screenshotPath, screenshot, 'base64');
  }
  
  static async waitForElement(driver, locator, timeout = SELENIUM_CONFIG.timeouts.element) {
    const { until } = require('selenium-webdriver');
    return await driver.wait(until.elementLocated(locator), timeout);
  }
  
  static async waitForElementVisible(driver, locator, timeout = SELENIUM_CONFIG.timeouts.element) {
    const { until } = require('selenium-webdriver');
    const element = await driver.wait(until.elementLocated(locator), timeout);
    await driver.wait(until.elementIsVisible(element), timeout);
    return element;
  }
  
  static async waitForText(driver, locator, text, timeout = SELENIUM_CONFIG.timeouts.element) {
    const { until } = require('selenium-webdriver');
    return await driver.wait(until.elementTextContains(locator, text), timeout);
  }
  
  static async scrollToElement(driver, element) {
    await driver.executeScript('arguments[0].scrollIntoView(true);', element);
    await driver.sleep(500); // Wait for scroll animation
  }
  
  static async measurePageLoad(driver, url) {
    const start = Date.now();
    await driver.get(url);
    const loadTime = Date.now() - start;
    
    // Get performance metrics
    const performanceMetrics = await driver.executeScript(`
      return {
        loadTime: ${loadTime},
        domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
        largestContentfulPaint: performance.getEntriesByName('largest-contentful-paint')[0]?.startTime || 0
      };
    `);
    
    return performanceMetrics;
  }
  
  static async checkAccessibility(driver) {
    if (!SELENIUM_CONFIG.accessibility.enabled) return null;
    
    // Inject axe-core for accessibility testing
    const axeCore = require('fs').readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
    await driver.executeScript(axeCore);
    
    // Run accessibility tests
    const results = await driver.executeScript(`
      return new Promise((resolve) => {
        axe.run(document, {
          tags: ['${SELENIUM_CONFIG.accessibility.standards.join("', '")}']
        }, (err, results) => {
          resolve(results);
        });
      });
    `);
    
    return results;
  }
  
  static async simulateNetworkConditions(driver, condition = 'slow3g') {
    const conditions = {
      slow3g: {
        downloadThroughput: 500 * 1024 / 8, // 500 kbps
        uploadThroughput: 500 * 1024 / 8,
        latency: 400
      },
      fast3g: {
        downloadThroughput: 1.6 * 1024 * 1024 / 8, // 1.6 Mbps
        uploadThroughput: 750 * 1024 / 8,
        latency: 150
      },
      slow4g: {
        downloadThroughput: 4 * 1024 * 1024 / 8, // 4 Mbps
        uploadThroughput: 3 * 1024 * 1024 / 8,
        latency: 20
      }
    };
    
    if (conditions[condition]) {
      await driver.executeScript(`
        // Simulate network conditions (Chrome DevTools API)
        window.chrome?.loadTimes && window.chrome.loadTimes();
      `);
    }
  }
}

// Test runner
class SeleniumTestRunner {
  constructor(config = {}) {
    this.config = { ...SELENIUM_CONFIG, ...config };
    this.driver = null;
    this.testResults = [];
  }
  
  async setup(browserName = 'firefox', headless = true) {
    this.driver = await DriverFactory.createDriver(browserName, headless);
    await this.driver.get(this.config.baseUrl);
  }
  
  async teardown() {
    if (this.driver) {
      await this.driver.quit();
    }
  }
  
  async runTest(testName, testFunction) {
    const startTime = Date.now();
    let result = { name: testName, status: 'passed', duration: 0, error: null };
    
    try {
      console.log(`Running test: ${testName}`);
      await testFunction(this.driver);
      
      if (this.config.screenshots.onSuccess) {
        await TestUtils.takeScreenshot(this.driver, `${testName}_success.png`);
      }
      
    } catch (error) {
      result.status = 'failed';
      result.error = error.message;
      
      if (this.config.screenshots.onFailure) {
        await TestUtils.takeScreenshot(this.driver, `${testName}_failure.png`);
      }
      
      console.error(`Test failed: ${testName}`, error);
    }
    
    result.duration = Date.now() - startTime;
    this.testResults.push(result);
    
    return result;
  }
  
  async runSuite(tests) {
    const results = [];
    
    for (const test of tests) {
      const result = await this.runTest(test.name, test.function);
      results.push(result);
    }
    
    return results;
  }
  
  generateReport() {
    const passed = this.testResults.filter(r => r.status === 'passed').length;
    const failed = this.testResults.filter(r => r.status === 'failed').length;
    const totalDuration = this.testResults.reduce((sum, r) => sum + r.duration, 0);
    
    return {
      summary: {
        total: this.testResults.length,
        passed,
        failed,
        duration: totalDuration,
        success: failed === 0
      },
      tests: this.testResults
    };
  }
}

module.exports = {
  SELENIUM_CONFIG,
  DriverFactory,
  TestUtils,
  SeleniumTestRunner
}; 