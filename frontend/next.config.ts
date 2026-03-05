import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /** Proxy API calls to the FastAPI backend during development */
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },

  /** Allow images from common AI/ML service domains */
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**.githubusercontent.com' },
      { protocol: 'https', hostname: '**.googleusercontent.com' },
    ],
  },
};

export default nextConfig;
