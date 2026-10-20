<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api, type StudyDocument, type DocumentPage } from '../lib/api'
import { message } from '../lib/state'
import { selectionError } from '../lib/documents'
export interface PdfSelection { documentId: string; startPage: number; endPage: number }
const props=defineProps<{modelValue:PdfSelection; disabled?:boolean}>()
const emit=defineEmits<{'update:modelValue':[value:PdfSelection];validation:[error:string]}>()
const documents=ref<StudyDocument[]>([]),pages=ref<DocumentPage[]>([]),loading=ref(false),error=ref('')
let generation=0
const validation=computed(()=>error.value || (loading.value?'正在读取教材页':!props.modelValue.documentId?'请选择教材':selectionError(pages.value,props.modelValue.startPage,props.modelValue.endPage)))
watch(validation,value=>emit('validation',value),{immediate:true})
function update(value:Partial<PdfSelection>){emit('update:modelValue',{...props.modelValue,...value})}
async function load(){const token=++generation;pages.value=[];error.value='';loading.value=false;if(!props.modelValue.documentId)return;loading.value=true;try{const data=await api.document(props.modelValue.documentId);if(token===generation)pages.value=data.pages}catch(e){if(token===generation)error.value=message(e)}finally{if(token===generation)loading.value=false}}
watch(()=>props.modelValue.documentId,load,{immediate:true})
async function list(){try{documents.value=(await api.documents()).documents}catch(e){error.value=message(e)}}
onMounted(list);onBeforeUnmount(()=>generation++)
</script>
<template><div class="document-range form-stack"><label>教材<select :value="modelValue.documentId" :disabled="disabled" @change="update({documentId:($event.target as HTMLSelectElement).value,startPage:1,endPage:1})"><option value="">选择自己的 PDF 教材</option><option v-for="document in documents" :key="document.id" :value="document.id">{{document.title}}（{{document.pageCount}} 页）</option></select></label><div class="form-columns"><label>起始物理页<input :value="modelValue.startPage" type="number" min="1" :max="pages.length||200" :disabled="disabled" @input="update({startPage:Number(($event.target as HTMLInputElement).value)})"/></label><label>结束物理页<input :value="modelValue.endPage" type="number" min="1" :max="pages.length||200" :disabled="disabled" @input="update({endPage:Number(($event.target as HTMLInputElement).value)})"/></label></div><p class="small muted">PDF 物理页从 1 开始，与印刷页码可能不同。每次最多 20 页、30000 字，不自动截断。</p><p v-if="modelValue.documentId && validation" class="error" role="status">{{validation}}</p><div class="row"><RouterLink to="/documents" class="text-button">管理教材</RouterLink><button v-if="error" type="button" class="text-button" @click="list();load()">重试读取</button></div></div></template>
