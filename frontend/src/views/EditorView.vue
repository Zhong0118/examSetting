<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { api, ApiError, type Question, type SetInput, type Citation, type QualityReport } from '../lib/api'
import { message, notify, user, registerIdentityGuard } from '../lib/state'
import Icon from '../components/Icon.vue'
import AIGenerator from '../components/AIGenerator.vue'
import CitationPicker from '../components/CitationPicker.vue'
import CitationCard from '../components/CitationCard.vue'
import QualityPanel from '../components/QualityPanel.vue'
import Pagination from '../components/Pagination.vue'
import { filterQuestions } from '../lib/question-browser'
const route=useRoute(),router=useRouter(),editing=!!route.params.id,loading=ref(editing),busy=ref(false),error=ref(''),conflict=ref(false),baseline=ref(''),canEdit=ref(!editing)
const editorRoot=ref<HTMLElement>()
const form=ref<SetInput>({title:'',description:'',topic:'',visibility:'private',questions:[]})
const search=ref(''),questionType=ref(''),questionTopic=ref(''),page=ref(1),pageSize=10,activeQuestion=ref<Question>()
const topics=computed(()=>[...new Set(form.value.questions.map(q=>q.topic).filter(Boolean))])
const filteredQuestions=computed(()=>{
  const rows=filterQuestions(form.value.questions,search.value,questionType.value,questionTopic.value)
  const index=form.value.questions.indexOf(activeQuestion.value!)
  if(index>=0&&!rows.some(row=>row.index===index))rows.push({question:form.value.questions[index],index})
  return rows.sort((a,b)=>a.index-b.index)
})
const currentPage=computed(()=>Math.min(page.value,Math.max(1,Math.ceil(filteredQuestions.value.length/pageSize))))
const pageQuestions=computed(()=>filteredQuestions.value.slice((currentPage.value-1)*pageSize,currentPage.value*pageSize))
watch([search,questionType,questionTopic],()=>{page.value=1;activeQuestion.value=undefined},{flush:'sync'})
watch(()=>form.value.questions,()=>showQuestion(0),{flush:'sync'})
function changePage(value:number){activeQuestion.value=undefined;page.value=value;activeQuestion.value=pageQuestions.value[0]?.question}
function showQuestion(index:number){search.value='';questionType.value='';questionTopic.value='';page.value=Math.max(1,Math.floor(index/pageSize)+1);activeQuestion.value=form.value.questions[index]}
function removeQuestion(index:number){const removed=form.value.questions.splice(index,1)[0];if(removed===citationQuestion.value)citationQuestion.value=undefined;if(removed===activeQuestion.value)showQuestion(Math.min(index,form.value.questions.length-1));else page.value=currentPage.value}
baseline.value=JSON.stringify(form.value)
const dirty=computed(()=>JSON.stringify(form.value)!==baseline.value)
const targetId=ref<string | undefined>(editing?String(route.params.id):undefined)
const recoveryKey=`examhub:editor:${user.value!.id}:${route.params.id || 'new'}`
function preserveEditor() {
  if(!dirty.value)return true
  try { localStorage.setItem(recoveryKey,JSON.stringify({form:form.value,targetId:targetId.value}));return true }
  catch { notify('无法保存编辑草稿，请先保留当前内容；账户暂未切换');return false }
}
const removeIdentityGuard=registerIdentityGuard(reason=>{
  if(reason==='preserve')return preserveEditor()
  if(busy.value){notify('题集正在保存，请等待完成后切换账户');return false}
  if(dirty.value && !window.confirm('切换账户前会保留当前编辑草稿。确定切换吗？'))return false
  return preserveEditor()
})
function restoreEditor() {
  try { const saved=JSON.parse(localStorage.getItem(recoveryKey)||'null');if(saved?.form?.title!==undefined && Array.isArray(saved.form.questions)){form.value=saved.form;targetId.value=saved.targetId || targetId.value;notify('已恢复当前账户的未保存编辑草稿')} } catch { /* Never delete unreadable recovery data. */ }
}
const citationQuestion=ref<Question>(),quality=ref<QualityReport>(),qualityBusy=ref(false),qualityError=ref(''),qualitySnapshot=ref('')
const initialDocumentId=String(route.query?.documentId||'')
const initialSelection={documentId:initialDocumentId,startPage:Number(route.query?.startPage)||1,endPage:Number(route.query?.endPage)||1}
const qualityStale=computed(()=>JSON.stringify(form.value.questions)!==qualitySnapshot.value)
function bindCitation(citation:Citation){if(citationQuestion.value){citationQuestion.value.citation=citation;citationQuestion.value.source=citation.quote}}
function removeCitation(q:Question){q.citation=null;q.source=''}
async function checkQuality(){qualityBusy.value=true;qualityError.value='';const snapshot=JSON.stringify(form.value.questions);try{quality.value=(await api.checkQuality(JSON.parse(snapshot))).report;qualitySnapshot.value=snapshot}catch(e){qualityError.value=message(e)}finally{qualityBusy.value=false}}
function blank(type:'single'|'short'='single'):Question{return {id:crypto.randomUUID(),type,prompt:'',options:type==='single'?['','']:[],answer:'',explanation:'',source:'',topic:''}}
function add(type:'single'|'short'){if(form.value.questions.length>=100){error.value='每份题集最多 100 道题';return}error.value='';form.value.questions.push(blank(type));showQuestion(form.value.questions.length-1)}
function changeType(q:Question){q.options=q.type==='single'?['','']:[];q.answer=''}
function importQuestions(questions:Question[],acknowledge:(accepted:boolean)=>void=()=>{}){
  if(form.value.questions.length+questions.length>100){error.value=`每份题集最多 100 道题，当前已有 ${form.value.questions.length} 道，本次 ${questions.length} 道未导入`;notify(error.value);acknowledge(false);return}
  if(!questions.length){acknowledge(false);return}
  const index=form.value.questions.length;form.value.questions.push(...questions);error.value='';showQuestion(index);acknowledge(true);notify(`已导入 ${questions.length} 道题，请检查并保存`)
}
function questionError(index:number,text:string){showQuestion(index);void nextTick(()=>editorRoot.value?.querySelector<HTMLElement>(`[data-question-index="${index}"] textarea`)?.focus());return `第 ${index+1} 题${text}`}
function validate(){
  if(!form.value.title.trim())return '请填写题集名称'
  if(form.value.title.length>200)return '题集名称不能超过 200 字'
  if(form.value.description.length>2000)return '题集简介不能超过 2000 字'
  if(form.value.topic.length>80)return '题集主题不能超过 80 字'
  if(!form.value.questions.length)return '请至少添加一道题'
  if(form.value.questions.length>100)return '每份题集最多 100 道题'
  for(const [i,q] of form.value.questions.entries()){
    if(!q.prompt.trim())return questionError(i,'缺少题干')
    for(const [key,label,limit] of [['prompt','题干',10000],['answer','答案',20000],['explanation','解析',20000],['source','出处',20000],['topic','知识点',20000]] as const){
      if((q[key]?.length||0)>limit)return questionError(i,`的${label}不能超过 ${limit} 字`)
    }
    if(q.options.length>10||q.options.some(o=>o.length>2000))return questionError(i,'的选项最多 10 个，每个不能超过 2000 字')
    if(q.type==='single'){
      if(q.options.length<2||q.options.some(o=>!o.trim()))return questionError(i,'至少需要两个非空选项')
      if(new Set(q.options.map(o=>o.trim())).size!==q.options.length)return questionError(i,'的选项不能重复')
      if(!q.options.includes(q.answer||''))return questionError(i,'请选择正确答案')
    }else if(!q.answer?.trim())return questionError(i,'请填写参考答案')
  }
  return ''
}
async function save(){
  if(!canEdit.value||busy.value)return
  error.value=validate();if(error.value)return
  busy.value=true
  const snapshot: SetInput=JSON.parse(JSON.stringify(form.value))
  try {
    const result=await api.save(snapshot,targetId.value)
    const unchanged=JSON.stringify(form.value)===JSON.stringify(snapshot)
    targetId.value=result.set.id
    form.value.version=result.set.version
    snapshot.version=result.set.version
    baseline.value=JSON.stringify(snapshot)
    if(!unchanged){preserveEditor();notify('已保存提交时的版本，后续修改仍在编辑器中，请再次保存');return}
    try{localStorage.removeItem(recoveryKey)}catch{}
    notify('题集已保存');await router.push(`/sets/${result.set.id}`)
  }catch(e){error.value=message(e);conflict.value=e instanceof ApiError&&e.status===409&&e.code!=='session_changed'}finally{busy.value=false}
}
async function load(restore=true){loading.value=true;error.value='';try{const {set}=await api.set(String(route.params.id));if(!set.isOwner){error.value='只有作者可以编辑题集';return}canEdit.value=true;form.value={title:set.title,description:set.description,topic:set.topic,visibility:set.visibility,version:set.version,questions:set.questions};baseline.value=JSON.stringify(form.value);conflict.value=false;if(restore)restoreEditor();else{try{localStorage.removeItem(recoveryKey)}catch{}}}catch(e){error.value=message(e)}finally{loading.value=false}}
function reload(){if(window.confirm('重新加载将丢弃当前未保存的修改，继续吗？'))return load(false)}
function beforeUnload(e:BeforeUnloadEvent){if(dirty.value){e.preventDefault();e.returnValue=''}}
onBeforeRouteLeave(()=>!dirty.value||window.confirm('当前题集有未保存的修改，确定离开吗？'))
onMounted(()=>{if(editing)load();else{form.value.questions=[blank()];baseline.value=JSON.stringify(form.value);restoreEditor()}window.addEventListener('beforeunload',beforeUnload)})
onBeforeUnmount(()=>{removeIdentityGuard();window.removeEventListener('beforeunload',beforeUnload)})
</script>
<template><div ref="editorRoot" class="page-container editor-page"><RouterLink :to="editing?`/sets/${route.params.id}`:'/library'" class="back-link"><Icon name="left"/>{{editing?'返回题集':'返回题库'}}</RouterLink><header class="page-heading"><div><h1>{{editing?'编辑题集':'创建一份题集'}}</h1><p>把值得记住的内容，变成值得思考的问题</p></div><span class="muted small">{{form.questions.length}} 道题 · {{dirty?'有未保存的修改':'准备就绪'}}</span></header><div v-if="loading" class="loading">正在读取题集…</div><div v-else-if="canEdit" class="editor-grid"><form novalidate @submit.prevent="save"><section class="surface form-stack"><h2>题集信息</h2><label>题集名称<input v-model="form.title" required maxlength="200" placeholder="例如：计算机网络 · 传输层基础"/></label><label>题集简介<textarea v-model="form.description" rows="2" maxlength="2000" placeholder="这份题集适合谁，希望理解哪些内容"/></label><div class="form-columns"><label>主题<input v-model="form.topic" maxlength="80" placeholder="例如：计算机网络"/></label><label>可见范围<select v-model="form.visibility"><option value="private">仅自己可见</option><option value="unlisted">持有链接的人可见</option><option value="public">公开到发现页</option></select></label></div><p class="muted small">{{form.visibility==='private'?'私有题集只有自己可以打开':form.visibility==='unlisted'?'不会出现在发现页，可将链接分享给他人':'其他人可以发现、练习并复制改编此题集'}}</p></section><div class="section-head questions-heading"><h2>编辑题目</h2><span class="small muted">单选自动判分 · 简答自行对照</span></div><section class="surface question-browser">
  <div class="section-head"><h3>题目目录</h3><span class="small muted">{{filteredQuestions.length}} / {{form.questions.length}} 道 · 每页 10 道 · 最多 100 道</span></div>
  <div class="question-browser-filters">
    <label class="question-search">搜索题目<input v-model="search" type="search" placeholder="搜索题干、知识点或选项"/></label>
    <label>题型筛选<select v-model="questionType"><option value="">全部题型</option><option value="single">单选题</option><option value="short">简答题</option></select></label>
    <label>知识点筛选<select v-model="questionTopic"><option value="">全部知识点</option><option v-for="topic in topics" :key="topic" :value="topic">{{topic}}</option></select></label>
  </div>
  <button v-if="search||questionType||questionTopic" type="button" class="text-button question-filter-reset" @click="search='';questionType='';questionTopic=''">清除筛选</button>
  <TransitionGroup name="list" tag="div" class="question-directory">
    <section v-for="({question:q,index}) in pageQuestions" :key="q.id" class="question-directory-item" :class="{'is-active':activeQuestion===q}">
      <button type="button" class="question-directory-toggle" :aria-label="`编辑第 ${index+1} 题`" :aria-expanded="activeQuestion===q" :aria-controls="`question-editor-${q.id}`" @click="activeQuestion=activeQuestion===q?undefined:q">
        <span class="editor-number">{{String(index+1).padStart(2,'0')}}</span>
        <span class="question-directory-summary"><span class="question-directory-title">{{q.prompt.trim()||'未填写题干'}}</span><span class="question-directory-meta">{{q.type==='single'?'单选题':'简答题'}} · {{q.topic||'未标注知识点'}}</span></span>
        <Icon :name="activeQuestion===q?'close':'edit'"/>
      </button>
      <Transition name="editor-detail"><div v-if="activeQuestion===q" :id="`question-editor-${q.id}`" :data-question-index="index" class="question-editor"><div class="section-head"><div class="row"><span class="editor-number">{{String(index+1).padStart(2,'0')}}</span><select v-model="q.type" :aria-label="`第 ${index+1} 题题型`" @change="changeType(q)"><option value="single">单选题</option><option value="short">简答题</option></select></div><button type="button" class="icon-button danger" :aria-label="`删除第 ${index+1} 题`" @click="removeQuestion(index)"><Icon name="delete"/></button></div><label>题干<textarea v-model="q.prompt" rows="3" required maxlength="10000" placeholder="写下一个清晰的问题"/></label><div v-if="q.type==='single'" class="editor-options"><p class="small muted">勾选左侧圆点，设为正确答案</p><div v-for="(_,i) in q.options" :key="i" class="editor-option"><input type="radio" :name="`answer-${q.id}`" :checked="q.answer===q.options[i] && !!q.options[i]" :aria-label="`选项 ${String.fromCharCode(65+i)} 为正确答案`" @change="q.answer=q.options[i]"/><span>{{String.fromCharCode(65+i)}}</span><input :value="q.options[i]" required maxlength="2000" :aria-label="`第 ${index+1} 题选项 ${String.fromCharCode(65+i)}`" placeholder="填写选项" @input="q.answer===q.options[i] && q.options[i] ? q.answer=($event.target as HTMLInputElement).value : null; q.options[i]=($event.target as HTMLInputElement).value"/><button type="button" class="icon-button" :disabled="q.options.length<=2" :aria-label="`删除选项 ${String.fromCharCode(65+i)}`" @click="q.answer===q.options[i] ? q.answer='' : null; q.options.splice(i,1)"><Icon name="close"/></button></div><button v-if="q.options.length<8" type="button" class="text-button" @click="q.options.push('')"><Icon name="plus"/>添加选项</button></div><label v-else>参考答案<textarea v-model="q.answer" required maxlength="20000" rows="3" placeholder="填写供学习者自评的参考答案"/></label><label>解析<textarea v-model="q.explanation" maxlength="20000" rows="2" placeholder="解释为什么，帮助建立理解"/></label><div class="form-columns"><label>知识点<input v-model="q.topic" maxlength="20000" placeholder="可选，如 TCP 拥塞控制"/></label><label>文本出处<input v-model="q.source" maxlength="20000" :readonly="!!q.citation" placeholder="可选，填写资料原文或出处"/></label></div><CitationCard v-if="q.citation" :citation="q.citation"/><div class="row"><button type="button" class="text-button" @click="citationQuestion=q"><Icon name="book"/>{{q.citation?'更换教材引文':'从教材绑定引文'}}</button><button v-if="q.citation" type="button" class="text-button danger" @click="removeCitation(q)">移除引用</button></div></div></Transition></section>
  </TransitionGroup>
  <p v-if="!filteredQuestions.length" class="muted question-browser-empty">{{form.questions.length?'没有匹配的题目，请调整筛选条件':'还没有题目，添加或导入后开始编辑'}}</p>
  <Pagination :page="currentPage" :total="filteredQuestions.length" :page-size="pageSize" label="题目目录" @change="changePage"/>
</section><div class="add-question"><button type="button" class="button" :disabled="form.questions.length>=100" @click="add('single')"><Icon name="plus"/>添加单选题</button><button type="button" class="button" :disabled="form.questions.length>=100" @click="add('short')"><Icon name="plus"/>添加简答题</button></div><div v-if="error" class="error" role="alert">{{error}}<button v-if="conflict" type="button" class="text-button" @click="reload">加载最新版本</button></div><section class="editor-quality"><div class="section-head"><h2>保存前检查</h2><button type="button" class="button" :disabled="qualityBusy||!form.questions.length" @click="checkQuality">{{qualityBusy?'正在检查…':'运行规则检查'}}</button></div><p class="muted small">不调用模型，检查题目结构、引用与重复候选。</p><p v-if="qualityError" class="error" role="alert">{{qualityError}}</p><QualityPanel v-if="quality" :report="quality" :stale="qualityStale"/></section><div class="save-bar"><span class="small muted">保存后才会更新题集</span><button class="button primary" :disabled="busy||loading">{{busy?'正在保存…':'保存题集'}}<Icon name="check"/></button></div></form><aside><AIGenerator :title="form.title" :topic="form.topic" :initial-selection="initialSelection" @import="importQuestions"/><div class="editor-tip"><Icon name="book"/><h3>好问题，留一点思考空间</h3><p>一次只考查一个概念。解析可以说明推理过程，帮助学习者理解答案背后的原因。</p></div></aside></div><div v-else class="error" role="alert">{{error}}<button class="text-button" @click="load()">重试</button></div><CitationPicker :open="!!citationQuestion" :citation="citationQuestion?.citation" :initial-document-id="initialDocumentId" @close="citationQuestion=undefined" @select="bindCitation"/></div></template>

<style scoped>
.question-browser{padding:20px}
.question-browser-filters{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr) minmax(0,1fr);gap:12px;margin:18px 0}
.question-browser-filters label{min-width:0}
.question-filter-reset{margin-bottom:12px}
.question-directory{display:flex;flex-direction:column;gap:8px}
.question-directory-item{min-width:0;border:1px solid #e4e4e7;border-radius:5px;transition:border-color .2s,background-color .2s}
.question-directory-item.is-active{border-color:#9cafd2;background:#fafafa}
.question-directory-toggle{display:flex;align-items:center;gap:14px;width:100%;padding:14px;text-align:left;border:0;border-radius:4px;background:transparent;cursor:pointer;transition:background-color .2s,transform .2s}
.question-directory-toggle:hover{background:#f4f4f5;transform:scale(1.005)}
.question-directory-toggle:active{transform:scale(.995)}
.question-directory-toggle:focus-visible{outline:2px solid #2563eb;outline-offset:2px}
.question-directory-summary{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}
.question-directory-title,.question-directory-meta{overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.question-directory-title{font-size:14px;font-weight:600;color:#18181b}
.question-directory-meta{font-size:12px;color:#71717a}
.question-directory-toggle>.editor-number{font-size:15px;min-width:24px;font-variant-numeric:tabular-nums}
.question-directory-toggle>:last-child{flex-shrink:0;color:#71717a}
.question-directory-item .question-editor{margin:0;padding:18px;border-top:1px solid #dbeafe}
.question-browser-empty{padding:24px 0;text-align:center}
.editor-detail-enter-active,.editor-detail-leave-active{interpolate-size:allow-keywords;transition:block-size .22s var(--ease),opacity .18s ease;overflow:clip}
.editor-detail-enter-from,.editor-detail-leave-to{block-size:0;opacity:0}
@media(max-width:640px){.question-browser{padding:14px}.question-browser-filters{grid-template-columns:1fr 1fr}.question-search{grid-column:1/-1}.question-directory-toggle{padding:12px;gap:10px}.question-directory-item .question-editor{padding:14px}}
@media(prefers-reduced-motion:reduce){.question-browser *{transition-duration:.01ms!important}}
</style>
