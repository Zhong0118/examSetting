<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { api, type Citation, type StudyDocument, type DocumentPage } from '../lib/api'
import { normalizeQuote } from '../lib/documents'
import { message } from '../lib/state'
import Modal from './Modal.vue'
const props=defineProps<{open:boolean;citation?:Citation|null;initialDocumentId?:string}>(),emit=defineEmits<{close:[];select:[citation:Citation]}>()
const documents=ref<StudyDocument[]>([]),documentId=ref(''),document=ref<StudyDocument>(),pages=ref<DocumentPage[]>([]),page=ref(1),quote=ref(''),loading=ref(false),error=ref(''),textPanel=ref<HTMLElement>()
let generation=0
const current=computed(()=>pages.value.find(p=>p.page===page.value))
const valid=computed(()=>!!document.value && !!normalizeQuote(quote.value) && normalizeQuote(current.value?.text||'').includes(normalizeQuote(quote.value)))
async function read(){const token=++generation;loading.value=true;error.value='';document.value=undefined;pages.value=[];try{if(!documentId.value)return;const data=await api.document(documentId.value);if(token!==generation)return;document.value=data.document;pages.value=data.pages;page.value=Math.min(data.document.pageCount,Math.max(1,page.value))}catch(e){if(token===generation)error.value=message(e)}finally{if(token===generation)loading.value=false}}
watch(documentId,read)
watch(()=>props.open,async open=>{if(!open){generation++;return}quote.value=props.citation?.quote||'';page.value=props.citation?.page||1;const id=props.citation?.documentId||props.initialDocumentId||'';if(documentId.value===id)void read();else documentId.value=id;try{documents.value=(await api.documents()).documents}catch(e){error.value=message(e)}})
function capture(){const selected=window.getSelection();if(selected&&textPanel.value?.contains(selected.anchorNode)&&textPanel.value.contains(selected.focusNode)&&selected.toString().trim())quote.value=selected.toString()}
function bind(){if(!valid.value||!document.value)return;emit('select',{documentId:document.value.id,documentTitle:document.value.title,documentHash:document.value.sha256,page:page.value,quote:quote.value});emit('close')}
onBeforeUnmount(()=>generation++)
</script>
<template><Modal :open="open" title="从教材绑定引文" @close="emit('close')"><div class="form-stack"><p class="muted small">选择自己的教材页，选取或粘贴逐字摘录。保存题集时由服务端核验页码、原文与文件哈希。</p><label>教材<select v-model="documentId"><option value="">选择教材</option><option v-for="doc in documents" :key="doc.id" :value="doc.id">{{doc.title}}</option></select></label><label>PDF 物理页<select v-model="page"><option v-for="item in pages" :key="item.page" :value="item.page">第 {{item.page}} 页（{{item.charCount}} 字）</option></select></label><div v-if="loading" class="loading">正在读取页文字…</div><div v-else ref="textPanel" tabindex="0" class="citation-source-text" aria-label="当前页原文，可选取文字" @mouseup="capture" @keyup="capture">{{current?.text||'当前页无可提取文字，请选择其他页。'}}</div><label>引用摘录<textarea v-model="quote" rows="4" placeholder="在上方选取文字，或粘贴本页原文"/></label><p v-if="quote&&!valid" class="error">摘录必须与所选页原文一致（允许空白与全半角规范化），请核对后再绑定。</p><p v-if="error" class="error" role="alert">{{error}}<button type="button" class="text-button" @click="read">重试</button></p><div class="modal-actions"><button type="button" class="button" @click="emit('close')">取消</button><button type="button" class="button primary" :disabled="!valid||loading" @click="bind">绑定本页引文</button></div></div></Modal></template>
