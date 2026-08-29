import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import node from '@astrojs/node';
import cloudflare from '@astrojs/cloudflare';

const isCloudflare = process.env.CF_PAGES === 'true' || process.env.BUILD_TARGET === 'cloudflare';

// https://astro.build/config
export default defineConfig({
  output: 'server',
  adapter: isCloudflare ? cloudflare() : node({ mode: 'standalone' }),
  vite: {
    plugins: [tailwindcss()],
    server: {
      watch: {
        // Exclude test scripts and non-source directories from HMR watching
        ignored: [
          '**/src/scripts/**',
          '**/node_modules/**',
          '**/.git/**',
          '**/dist/**',
        ]
      }
    }
  },
});
