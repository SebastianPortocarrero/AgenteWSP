/** @type {import('jest').Config} */
export default {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  
  // Module paths
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/services/(.*)$': '<rootDir>/src/services/$1',
    '^@/hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@/utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@/types/(.*)$': '<rootDir>/src/types/$1',
    '^@/stores/(.*)$': '<rootDir>/src/stores/$1',
    '^@/constants/(.*)$': '<rootDir>/src/constants/$1',
    '^@/assets/(.*)$': '<rootDir>/src/assets/$1',
    
    // CSS modules
    '\\.(css|less|sass|scss)$': 'identity-obj-proxy',
    
    // Static assets
    '\\.(png|jpg|jpeg|gif|svg|ico)$': '<rootDir>/src/__mocks__/fileMock.js',
    
    // Font files
    '\\.(woff|woff2|eot|ttf|otf)$': '<rootDir>/src/__mocks__/fileMock.js'
  },
  
  // File extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  
  // Transform files
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  
  // Ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(jose|jwt-decode|@faker-js/faker|web-vitals)/)'
  ],
  
  // Test patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}',
    '<rootDir>/tests/**/*.{test,spec}.{ts,tsx}'
  ],
  
  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
    '!src/setupTests.ts',
    '!src/**/__tests__/**',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/**/__mocks__/**',
    '!src/**/types.ts',
    '!src/**/index.ts',
    '!src/assets/**',
    '!src/public/**'
  ],
  
  // Coverage thresholds - 85% requirement
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    // Specific thresholds for critical components
    'src/components/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    'src/services/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    'src/hooks/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    'src/utils/': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'text-summary',
    'lcov',
    'html',
    'json',
    'clover'
  ],
  
  // Coverage directory
  coverageDirectory: 'coverage',
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Restore mocks after each test
  restoreMocks: true,
  
  // Error handling
  errorOnDeprecated: true,
  
  // Globals
  globals: {
    'ts-jest': {
      useESM: true,
      tsconfig: {
        jsx: 'react-jsx'
      }
    }
  },
  
  // Test reporters
  reporters: [
    'default',
    ['jest-html-reporter', {
      'pageTitle': 'Tony WhatsApp Assistant - Frontend Test Report',
      'outputPath': 'test-report.html',
      'includeFailureMsg': true,
      'includeSuiteFailure': true,
      'includeConsoleLog': true,
      'logo': 'src/assets/logo.png'
    }]
  ],
  
  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Max workers
  maxWorkers: '50%',
  
  // Preset
  preset: 'ts-jest/presets/default-esm',
  
  // ESM support
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  
  // Additional test environment options
  testEnvironmentOptions: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  },
  
  // Snapshot options
  snapshotSerializers: ['enzyme-to-json/serializer'],
  
  // Additional setup
  globalSetup: '<rootDir>/tests/setup/globalSetup.ts',
  globalTeardown: '<rootDir>/tests/setup/globalTeardown.ts',
  
  // Project-specific configuration
  projects: [
    {
      displayName: 'unit',
      testMatch: ['<rootDir>/src/**/__tests__/**/*.unit.{ts,tsx}'],
      testEnvironment: 'jsdom'
    },
    {
      displayName: 'integration',
      testMatch: ['<rootDir>/src/**/__tests__/**/*.integration.{ts,tsx}'],
      testEnvironment: 'jsdom'
    },
    {
      displayName: 'security',
      testMatch: ['<rootDir>/tests/security/**/*.{ts,tsx}'],
      testEnvironment: 'jsdom'
    }
  ]
}; 