/** @type {import('next').NextConfig} */

// 前端浏览器侧默认走相对路径（即调用 /api/...，再由 Next.js rewrite 转发）。
// rewrite 的实际目标由 API_BACKEND_URL 控制（服务端环境变量，不暴露给浏览器）。
const BACKEND = process.env.API_BACKEND_URL || "http://localhost:8080";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
