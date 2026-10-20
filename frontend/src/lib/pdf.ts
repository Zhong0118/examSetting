import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
GlobalWorkerOptions.workerSrc=workerUrl
export function loadPdf(data: ArrayBuffer) {
  const assets=`${import.meta.env.BASE_URL}pdfjs-assets/`
  return getDocument({data:new Uint8Array(data),cMapUrl:`${assets}cmaps/`,cMapPacked:true,standardFontDataUrl:`${assets}standard_fonts/`,wasmUrl:`${assets}wasm/`})
}
