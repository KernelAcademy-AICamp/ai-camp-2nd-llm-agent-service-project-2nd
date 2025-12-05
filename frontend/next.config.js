/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static HTML Export for S3/CloudFront deployment
  // 개발 모드에서는 비활성화 (미들웨어 사용 위해)
  ...(process.env.NODE_ENV === 'production' && { output: 'export' }),

  // Disable image optimization for static export (use external CDN or unoptimized)
  images: {
    unoptimized: true,
  },

  // Trailing slash for S3 compatibility
  trailingSlash: true,

  // Base path (change if deploying to subdirectory)
  // basePath: '',

  // Asset prefix for CDN (CloudFront)
  // assetPrefix: process.env.NEXT_PUBLIC_CDN_URL || '',

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '0.2.0',
    NEXT_PUBLIC_BUILD_TIME: new Date().toISOString(),
  },

  // Strict mode for React
  reactStrictMode: true,

  // TypeScript and ESLint configuration
  typescript: {
    // Allow production builds even with type errors (for gradual migration)
    ignoreBuildErrors: false,
  },
  eslint: {
    // Run ESLint during builds
    ignoreDuringBuilds: false,
  },

  // Experimental features
  experimental: {
    // Enable server actions if needed in future
    // serverActions: true,
  },

  // Webpack customization
  webpack: (config, { isServer }) => {
    // Add any custom webpack config here
    return config;
  },
};

module.exports = nextConfig;
