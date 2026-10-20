<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { PDFDocumentProxy, PDFDocumentLoadingTask, RenderTask } from 'pdfjs-dist'
import { api } from '../lib/api'
import { message } from '../lib/state'
const props=defineProps<{documentId:string;page:number}>()
const canvas=ref<HTMLCanvasElement>(),container=ref<HTMLElement>(),busy=ref(true),error=ref('')
let pdf:PDFDocumentProxy|undefined,task:PDFDocumentLoadingTask|undefined,renderTask:RenderTask|undefined,observer:ResizeObserver|undefined,loadVersion=0,renderVersion=0,disposed=false
async function render(){
  const version=++renderVersion,previous=renderTask;previous?.cancel();if(previous)await previous.promise.catch(()=>{})
  if(!pdf||!canvas.value||disposed||version!==renderVersion)return
  busy.value=true;error.value=''
  try{
    const page=await pdf.getPage(props.page);if(disposed||version!==renderVersion||!canvas.value)return
    const base=page.getViewport({scale:1}),width=Math.max(180,(container.value?.clientWidth||600)-24),scale=Math.min(1.5,width/base.width)
    const viewport=page.getViewport({scale}),ratio=Math.min(window.devicePixelRatio||1,2)
    canvas.value.width=Math.ceil(viewport.width*ratio);canvas.value.height=Math.ceil(viewport.height*ratio)
    canvas.value.style.width=`${viewport.width}px`;canvas.value.style.height=`${viewport.height}px`
    renderTask=page.render({canvas:canvas.value,viewport,transform:ratio===1?undefined:[ratio,0,0,ratio,0,0]})
    await renderTask.promise
  }catch(e){if(!disposed&&version===renderVersion)error.value=message(e)}finally{if(version===renderVersion)busy.value=false}
}
async function load(){
  const version=++loadVersion;renderVersion++;renderTask?.cancel();await task?.destroy();pdf=undefined;error.value='';busy.value=true
  try{const [module,file]=await Promise.all([import('../lib/pdf'),api.documentFile(props.documentId)]);const data=await file.arrayBuffer();if(disposed||version!==loadVersion)return;const loading=module.loadPdf(data);task=loading;const document=await loading.promise;if(disposed||version!==loadVersion){await loading.destroy();return}pdf=document;await nextTick();await render()}
  catch(e){if(!disposed&&version===loadVersion){error.value=message(e);busy.value=false}}
}
watch(()=>props.documentId,load);watch(()=>props.page,render)
onMounted(()=>{void load();observer=new ResizeObserver(()=>{if(pdf)void render()});if(container.value)observer.observe(container.value)})
onBeforeUnmount(()=>{disposed=true;loadVersion++;renderVersion++;observer?.disconnect();renderTask?.cancel();void task?.destroy()})
</script>
<template><section ref="container" class="pdf-original" aria-label="PDF 原文件页面"><div v-if="busy" class="pdf-status" role="status">正在渲染原页…</div><div v-if="error" class="error" role="alert">原 PDF 暂时无法显示：{{error}}<button class="text-button" @click="load">重新读取原文件</button></div><canvas ref="canvas" :aria-label="`PDF 第 ${page} 物理页；可在右侧读取对应文字`" role="img"/></section></template>
