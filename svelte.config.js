import adapter from '@sveltejs/adapter-vercel';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      runtime: 'nodejs20.x',
      isr: {
        expiration: 60,
        bypassToken: process.env.ISR_BYPASS_TOKEN,
      },
    }),
    csrf: { checkOrigin: false },
  },
};

export default config;
