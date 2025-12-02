import next from 'eslint-config-next';

export default [
  {
    ignores: [
      '**/node_modules/**',
      '.next',
      'out',
      'coverage',
      'playwright-report',
      'test-results',
      'e2e/.playwright-cache',
    ],
  },
  ...next,
];
