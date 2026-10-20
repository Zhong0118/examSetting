<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { api, type Job, type Question, type AIConfig } from '../lib/api'
import { message, user } from '../lib/state'
import Icon from './Icon.vue'
import DocumentRange, { type PdfSelection } from './DocumentRange.vue'
import QualityPanel from './QualityPanel.vue'
const props=defineProps<{title:string;topic:string;initialSelection?:PdfSelection}>(), emit=defineEmits<{import:[questions:Question[]]}>()
const source=ref(''), count=ref(5), config=ref<AIConfig>(), job=ref<Job>(), error=ref(''), busy=ref(false), imported=ref(false)
const sourceMode=ref(props.initialSelection?.documentId?'pdf':'text'),pdfSelection=ref<PdfSelection>(props.initialSelection||{documentId:'',startPage:1,endPage:1}),documentError=ref('请选择教材')
const active=computed(()=>job.value?.status==='queued'||job.value?.status==='running')
const storageKey=`examhub:ai-job:${user.value?.id}`
let timer:ReturnType<typeof setTimeout>, disposed=false, generation=0, pollSequence=0
const labels={queued:'任务已排队',running:'正在根据资料生成题目',completed:'题目已生成，请检查后导入',failed:'生成失败',cancelled:'任务已取消'}
function remember(){try{if(job.value)localStorage.setItem(storageKey,job.value.id)}catch{/* Persistence is optional. */}}
function schedule(){clearTimeout(timer);if(active.value&&!disposed)timer=setTimeout(poll,1800)}
async function poll(){
  if(!job.value||disposed)return
  const id=job.value.id, token=generation, sequence=++pollSequence
  const current=()=>!disposed && token===generation && sequence===pollSequence && job.value?.id===id
  try{const result=await api.job(id);if(!current())return;job.value=result.job;error.value='';schedule()}
  catch(e){if(current())error.value=message(e)}
}
async function start(){
  if(busy.value||active.value||disposed)return
  error.value=''
  if((sourceMode.value==='text'&&(source.value.length<20||source.value.length>30000))||!Number.isInteger(count.value)||count.value<1||count.value>10){error.value='请填写 20–30000 字资料，题数为 1–10 的整数';return}
  if(sourceMode.value==='pdf'&&documentError.value){error.value=documentError.value;return}
  const token=++generation;clearTimeout(timer);busy.value=true;imported.value=false
  try{const result=await api.startJob({...(sourceMode.value==='pdf'?{...pdfSelection.value,strategy:'grounded' as const}:{source:source.value}),title:props.title,topic:props.topic,count:count.value});if(disposed||token!==generation)return;job.value=result.job;remember();schedule()}
  catch(e){if(!disposed&&token===generation)error.value=message(e)}
  finally{if(!disposed&&token===generation)busy.value=false}
}
async function cancel(){
  if(!job.value||busy.value||disposed)return
  const id=job.value.id, token=++generation;clearTimeout(timer);busy.value=true
  try{const result=await api.cancelJob(id);if(disposed||token!==generation)return;job.value=result.job;schedule()}
  catch(e){if(!disposed&&token===generation){error.value=message(e);schedule()}}
  finally{if(!disposed&&token===generation)busy.value=false}
}
function importQuestions(){if(job.value?.status!=='completed'||imported.value)return;emit('import',job.value.questions.map(q=>({...q,id:crypto.randomUUID()})));imported.value=true;try{localStorage.removeItem(storageKey)}catch{}}
onMounted(async()=>{
  const token=generation
  try{const settings=await api.config();if(disposed||token!==generation)return;config.value=settings;const key=localStorage.getItem(storageKey);if(key){const result=await api.job(key);if(disposed||token!==generation)return;job.value=result.job;schedule()}}
  catch(e){if(!disposed&&token===generation)error.value=message(e)}
})
onBeforeUnmount(()=>{disposed=true;generation++;clearTimeout(timer)})
</script>
<template><section class="ai-panel"><div class="section-head"><h3><Icon name="ai"/>从资料生成题目</h3><span class="badge">AI 辅助</span></div><p class="muted small">粘贴可信资料，生成后先检查题干、答案和原文引用，再导入题集。</p><p v-if="config && !config.configured" class="inline-note">还未配置模型密钥。<RouterLink to="/settings">前往模型设置</RouterLink></p><div class="tabs source-tabs" aria-label="资料来源" :style="{'--tab-index':sourceMode==='pdf'?1:0}"><button type="button" :class="{active:sourceMode==='text'}" :aria-pressed="sourceMode==='text'" :disabled="active||busy" @click="sourceMode='text'">粘贴资料</button><button type="button" :class="{active:sourceMode==='pdf'}" :aria-pressed="sourceMode==='pdf'" :disabled="active||busy" @click="sourceMode='pdf'">PDF 教材</button></div><div class="form-stack"><DocumentRange v-if="sourceMode==='pdf'" v-model="pdfSelection" :disabled="active||busy" @validation="documentError=$event"/><label v-else>学习资料<textarea v-model="source" rows="7" minlength="20" maxlength="30000" :disabled="active" placeholder="粘贴 20–30000 字学习资料，引用将与原文核对"/></label><div class="row between"><label>生成题数<input v-model.number="count" type="number" min="1" max="10" :disabled="active"/></label><span v-if="sourceMode==='text'" class="small muted">{{source.length}} / 30000 字</span></div><button type="button" class="button primary" :disabled="busy||active||!config?.configured" @click="start"><Icon name="ai"/>{{busy?'正在请求…':'生成题目'}}</button></div><div v-if="job" class="job-status" aria-live="polite"><div class="row"><span v-if="active" class="spinner"/><strong>{{labels[job.status]}}</strong></div><p v-if="job.error" class="error">{{job.error}}</p><p v-if="active" class="muted small">任务在后台运行，返回编辑器后可继续查看。</p><button type="button" v-if="active" class="text-button" :disabled="busy" @click="cancel">取消生成</button><template v-if="job.status==='completed'"><p class="small">生成了 {{job.questions.length}} 道题，导入后仍需保存题集</p><details><summary>预览生成内容</summary><div v-for="(q,i) in job.questions" :key="q.id" class="ai-preview"><strong>{{i+1}}. {{q.prompt}}</strong><p>参考答案：{{q.answer}}</p><p v-if="q.citation" class="source-text">{{q.citation.documentTitle}} · 物理页 {{q.citation.page}}<br/>{{q.citation.quote}}</p><p v-else-if="q.source" class="source-text">文本出处：{{q.source}}</p><p v-else class="small muted">未提供可验证引用</p></div></details><QualityPanel v-if="job.quality" :report="job.quality"/><button type="button" class="button" :disabled="imported||!job.questions.length" @click="importQuestions">{{imported?'已导入编辑器':'导入生成题目'}}</button></template></div><p v-if="error" class="error" role="alert">{{error}}<button type="button" v-if="active" class="text-button" @click="poll">重新获取任务</button></p></section></template>
