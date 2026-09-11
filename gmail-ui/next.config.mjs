/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  experimental: {
    // Avoid native lightningcss binary; use PostCSS instead
    optimizeCss: false,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
