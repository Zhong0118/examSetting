<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type SetDetail, type QualityReport } from '../lib/api'
import { date, message, notify, visibilityLabels } from '../lib/state'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'
import CitationCard from '../components/CitationCard.vue'
import QualityPanel from '../components/QualityPanel.vue'
import Pagination from '../components/Pagination.vue'
import { filterQuestions } from '../lib/question-browser'
const route=useRoute(), router=useRouter(), set=ref<SetDetail>(), error=ref(''), busy=ref(''), remove=ref(false), share=ref(false), shareUrl=ref('')
const quality=ref<QualityReport>(),qualityBusy=ref(false)
const search=ref(''),typeFilter=ref(''),topicFilter=ref(''),page=ref(1),pageSize=10
const questionTopics=computed(()=>[...new Set(set.value?.questions.map(q=>q.topic).filter(Boolean)||[])])
const filteredQuestions=computed(()=>filterQuestions(set.value?.questions||[],search.value,typeFilter.value,topicFilter.value))
const pageCount=computed(()=>Math.max(1,Math.ceil(filteredQuestions.value.length/pageSize)))
const visibleQuestions=computed(()=>filteredQuestions.value.slice((page.value-1)*pageSize,page.value*pageSize))
watch([search,typeFilter,topicFilter],()=>page.value=1)
watch(pageCount,count=>page.value=Math.min(page.value,count))
let generation=0,disposed=false
async function checkQuality(){
  if(!set.value||qualityBusy.value)return
  const {id,version}=set.value,token=generation
  const active=()=>!disposed&&token===generation&&String(route.params.id)===id&&set.value?.version===version
  qualityBusy.value=true
  try{
    const data=await api.setQuality(id)
    if(!active())return
    if(data.version!==version){quality.value=undefined;notify('题集已更新，正在加载最新版本，请重新检查');await load();return}
    quality.value=data.report
  }catch(e){if(active())notify(message(e))}finally{if(!disposed)qualityBusy.value=false}
}
async function load(){const token=++generation,id=String(route.params.id);quality.value=undefined;error.value='';try{const data=await api.set(id);if(!disposed&&token===generation&&String(route.params.id)===id)set.value=data.set}catch(e){if(!disposed&&token===generation)error.value=message(e)}}
onBeforeUnmount(()=>{disposed=true;generation++})
async function action(kind:string){if(!set.value||busy.value)return;busy.value=kind;try{if(kind==='bookmark'){set.value.bookmarked=(await api.bookmark(set.value.id)).bookmarked;notify(set.value.bookmarked?'已收藏题集':'已取消收藏')}if(kind==='fork'){const copy=(await api.fork(set.value.id)).set;notify('已复制为私有题集');await router.push(`/sets/${copy.id}/edit`)}if(kind==='delete'){await api.delete(set.value.id);remove.value=false;notify('题集已删除');await router.push('/library')}if(kind==='share'){shareUrl.value=`${location.origin}/sets/${set.value.id}`;try{await navigator.clipboard.writeText(shareUrl.value);notify('题集链接已复制')}catch{share.value=true}}if(kind==='export'){const {Document,Packer,Paragraph,HeadingLevel}=await import('docx');const paragraphs=[new Paragraph({text:set.value.title,heading:HeadingLevel.TITLE}),new Paragraph(set.value.description)];set.value.questions.forEach((q,i)=>{paragraphs.push(new Paragraph({text:`${i+1}. ${q.prompt}`,heading:HeadingLevel.HEADING_2}),...q.options.map((o,j)=>new Paragraph(`${String.fromCharCode(65+j)}. ${o}`)));if(q.answer!==undefined)paragraphs.push(new Paragraph(`参考答案：${q.answer}`));if(q.explanation)paragraphs.push(new Paragraph(`解析：${q.explanation}`));if(q.source)paragraphs.push(new Paragraph(`出处：${q.source}`))});const blob=await Packer.toBlob(new Document({sections:[{children:paragraphs}]}));const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`${set.value.title.replace(/[\\/:*?"<>|]/g,'_')}.docx`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('Word 文件已导出')}}catch(e){notify(message(e))}finally{busy.value=''}}
onMounted(load)
</script>
<template><div class="page-container detail-page"><RouterLink to="/library" class="back-link"><Icon name="left"/>返回题库</RouterLink><div v-if="error" class="empty-state"><h2>无法打开题集</h2><p>{{error}}</p><button class="button" @click="load">重试</button></div><div v-else-if="!set" class="loading">正在打开题集…</div><template v-else><header class="detail-header"><div><span class="topic-label">{{set.topic||'综合学习'}}</span><h1>{{set.title}}</h1><p class="description">{{set.description||'从一道题开始，建立自己的理解'}}</p><div class="set-meta"><span>{{set.author}}</span><span>{{set.questionCount}} 道题</span><span>{{visibilityLabels[set.visibility]}}</span><span>版本 {{set.version}} · {{date(set.updatedAt)}}更新</span></div><p v-if="set.sourceSetId" class="small muted">改编自题集 <RouterLink :to="`/sets/${set.sourceSetId}`">查看原题集</RouterLink>（原题集仍需访问权限）</p></div><RouterLink :to="`/practice/${set.id}`" class="button primary large">开始练习<Icon name="right"/></RouterLink></header><div class="action-bar"><RouterLink :to="`/tutor?setId=${set.id}`" class="button"><Icon name="ai"/>教学教练</RouterLink><RouterLink v-if="set.isOwner" :to="`/sets/${set.id}/edit`" class="button"><Icon name="edit"/>编辑题集</RouterLink><button class="button" :disabled="!!busy" @click="action('bookmark')"><Icon name="star"/>{{set.bookmarked?'已收藏':'收藏题集'}}</button><button class="button" :disabled="!!busy" @click="action('share')"><Icon name="share"/>复制链接</button><button class="button" :disabled="!!busy" @click="action('fork')"><Icon name="copy"/>复制改编</button><button class="button" :disabled="!!busy" @click="action('export')"><Icon name="download"/>导出 Word</button><button v-if="set.isOwner" class="icon-button danger" aria-label="删除题集" :disabled="!!busy" @click="remove=true"><Icon name="delete"/></button></div><p v-if="set.visibility==='private'" class="inline-note"><Icon name="lock"/>当前为私有题集，复制链接后其他人仍无法访问。可在编辑页改为链接可见或公开。</p><section v-if="set.isOwner" class="detail-quality"><div class="section-head"><h2>规则质量检查</h2><button class="button" :disabled="qualityBusy" @click="checkQuality">{{qualityBusy?'正在检查…':'检查当前版本'}}</button></div><QualityPanel v-if="quality" :report="quality"/></section><section class="question-browser">
<div class="section-head"><h2>题目目录</h2><span class="muted small">共 {{set.questions.length}} 题 · {{set.isOwner?'展开查看题目与参考答案':'提交练习后查看参考答案'}}</span></div>
<div class="question-toolbar"><label class="search-field"><Icon name="search"/><input v-model="search" aria-label="搜索题目" placeholder="搜索题干 选项或知识点"/></label><select v-model="typeFilter" aria-label="筛选题型"><option value="">全部题型</option><option value="single">单选题</option><option value="short">简答题</option></select><select v-model="topicFilter" aria-label="筛选知识点"><option value="">全部知识点</option><option v-for="item in questionTopics" :key="item">{{item}}</option></select></div>
<TransitionGroup name="collection" tag="div" class="question-catalog">
<details v-for="{question,index} in visibleQuestions" :key="question.id" class="question-catalog-row">
<summary><span class="question-index">{{String(index+1).padStart(2,'0')}}</span><span class="question-overview"><strong>{{question.prompt}}</strong><span>{{question.type==='single'?'单选题':'简答题'}}<template v-if="question.topic"> · {{question.topic}}</template></span></span><Icon name="right" class="question-chevron"/></summary>
<div class="question-expanded"><h3>{{question.prompt}}</h3><ul v-if="question.options.length" class="preview-options"><li v-for="(option,i) in question.options" :key="i"><span>{{String.fromCharCode(65+i)}}</span>{{option}}</li></ul><details v-if="set.isOwner&&question.answer!==undefined"><summary>查看参考答案与解析</summary><p class="answer-text">{{question.answer}}</p><p>{{question.explanation}}</p></details><CitationCard v-if="question.citation" :citation="question.citation"/><p v-else-if="question.source" class="source-text">出处：{{question.source}}</p></div>
</details>
</TransitionGroup>
<div v-if="!filteredQuestions.length" class="empty-state compact"><h3>没有匹配的题目</h3><button class="button" @click="search='';typeFilter='';topicFilter=''">清除筛选</button></div>
<Pagination :page="page" :total="filteredQuestions.length" :page-size="pageSize" label="题目分页" @change="page=$event"/>
</section></template><Modal :open="remove" title="删除这份题集？" @close="remove=false"><p>删除后无法继续访问题集，已完成的学习记录保留。</p><div class="modal-actions"><button class="button" @click="remove=false">保留题集</button><button class="button danger-fill" :disabled="!!busy" @click="action('delete')">{{busy?'正在删除…':'删除题集'}}</button></div></Modal><Modal :open="share" title="复制题集链接" @close="share=false"><p class="muted">浏览器暂不允许自动复制，请选择下面的链接手动复制</p><input :value="shareUrl" readonly aria-label="题集分享链接" @focus="($event.target as HTMLInputElement).select()"/></Modal></div></template>

<style scoped>
.question-browser>.section-head{flex-wrap:wrap;gap:6px}
.question-toolbar{display:flex;gap:8px;margin-bottom:12px}
.question-toolbar select{width:auto;max-width:180px;font-size:12px}
.question-catalog{position:relative;border-top:1px solid var(--line)}
.question-catalog-row{border-bottom:1px solid var(--line)}
.question-catalog-row>summary{display:flex;align-items:center;gap:12px;padding:12px 4px;list-style:none;border-radius:4px;transition:background .18s}
.question-catalog-row>summary::-webkit-details-marker{display:none}
.question-catalog-row>summary:hover{background:#fafafa}
.question-index{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;min-width:24px}
.question-overview{flex:1;min-width:0;display:flex;flex-direction:column;gap:3px}
.question-overview strong{font-size:13px;font-weight:550;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.question-overview>span{font-size:12px;color:var(--muted)}
.question-chevron{width:14px;height:14px;color:var(--muted);transition:transform .22s var(--ease)}
.question-catalog-row[open] .question-chevron{transform:rotate(90deg)}
.question-expanded{padding:8px 28px 18px 40px;font-size:13px;overflow-wrap:anywhere}
.question-expanded h3{font-size:14px;font-weight:550;margin-bottom:14px;white-space:pre-wrap}
@media(max-width:760px){.question-toolbar{flex-wrap:wrap}.question-toolbar .search-field{flex-basis:100%}.question-toolbar select{flex:1;max-width:none}.question-expanded{padding-left:4px;padding-right:4px}}
</style>
