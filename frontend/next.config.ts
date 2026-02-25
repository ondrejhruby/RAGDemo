import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const target = process.env.NEXT_PUBLIC_API_URL ?? "http://backend:8000";
    return [
      {
        source: "/api/backend/:path*",
        destination: `${target}/:path*`,
      },
    ];
  },
};

export default nextConfig;


