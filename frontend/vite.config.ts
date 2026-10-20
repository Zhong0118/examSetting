import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { readdirSync, readFileSync } from 'node:fs'
const pdfRoot=dirname(createRequire(import.meta.url).resolve('pdfjs-dist/package.json'))
const pdfAssets=new Map<string,Buffer>([['/pdfjs-assets/LICENSE',readFileSync(join(pdfRoot,'LICENSE'))]])
for(const folder of ['cmaps','standard_fonts','wasm'])for(const file of readdirSync(join(pdfRoot,folder)))pdfAssets.set(`/pdfjs-assets/${folder}/${file}`,readFileSync(join(pdfRoot,folder,file)))


// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name:'local-pdf-assets',
      configureServer(server) { server.middlewares.use((req,res,next)=>{const pathname=req.url?.split('?')[0]||'';const data=pdfAssets.get(pathname);if(!data)return next();res.setHeader('Content-Type',pathname.endsWith('.wasm')?'application/wasm':pathname.endsWith('.js')?'application/javascript':'application/octet-stream');res.end(data)}) },
      generateBundle() { for(const [path,source] of pdfAssets)this.emitFile({type:'asset',fileName:path.slice(1),source}) },
    },
  ],
  server: { proxy: { '/api': { target: 'http://127.0.0.1:5000', changeOrigin: false } } },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
