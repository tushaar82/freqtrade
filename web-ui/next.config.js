/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Allow API calls to localhost (Freqtrade and OpenAlgo)
  async rewrites() {
    return [
      {
        source: '/api/freqtrade/:path*',
        destination: 'http://localhost:8080/api/v1/:path*',
      },
      {
        source: '/api/openalgo/:path*',
        destination: 'http://localhost:5000/api/v1/:path*',
      },
    ];
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_FREQTRADE_API_URL: process.env.NEXT_PUBLIC_FREQTRADE_API_URL || 'http://localhost:8080/api/v1',
    NEXT_PUBLIC_OPENALGO_API_URL: process.env.NEXT_PUBLIC_OPENALGO_API_URL || 'http://localhost:5000/api/v1',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080/ws',
  },

  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Image optimization
  images: {
    domains: ['localhost'],
  },
};

module.exports = nextConfig;
