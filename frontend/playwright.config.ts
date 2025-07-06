// Simplified Playwright Configuration for Tony WhatsApp Assistant
// Firefox-only testing configuration without external dependencies

export default {
  testDir: './tests/e2e',
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: false,
  
  /* Retry configuration */
  retries: 2,
  
  /* Workers configuration */
  workers: 1,
  
  /* Reporter to use */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }]
  ],
  
  /* Shared settings for all the projects */
  use: {
    /* Base URL to use in actions like await page.goto('/') */
    baseURL: 'http://localhost:3000',
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Take screenshot only when test fails */
    screenshot: 'only-on-failure',
    
    /* Record video only when retrying */
    video: 'retain-on-failure',
    
    /* Action timeout */
    actionTimeout: 10000,
    
    /* Navigation timeout */
    navigationTimeout: 30000,
    
    /* Expect timeout */
    expectTimeout: 5000,
  },
  
  /* Configure projects for Firefox only */
  projects: [
    {
      name: 'firefox',
      use: { 
        browserName: 'firefox',
        viewport: { width: 1920, height: 1080 }
      },
    },
    
    /* Test against mobile viewports with Firefox */
    {
      name: 'Mobile Firefox',
      use: { 
        browserName: 'firefox',
        viewport: { width: 390, height: 844 }
      },
    },
  ],
  
  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
  
  /* Output directory for artifacts */
  outputDir: './test-results/',
  
  /* Maximum time one test can run for */
  timeout: 30 * 1000,
  
  /* Expect timeout */
  expect: {
    timeout: 5000,
  },
}; 