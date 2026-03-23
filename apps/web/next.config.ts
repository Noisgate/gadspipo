import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@adsmcp/domain", "@adsmcp/prompts", "@adsmcp/ui"],
};

export default nextConfig;
