<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type AIConfig, type SetSummary } from '../lib/api'
import { tutorApi, tutorMode, tutorStatus, type TutorMode, type TutorSummary } from '../lib/tutor'
import { createTutorRequest, type PendingTutorRequest } from '../lib/tutorRequests'
import { user, sessionFrozen, identityChanging, message, notify, registerIdentityGuard, date } from '../lib/state'
import { downloadJSON } from '../lib/documents'
import Icon from '../components/Icon.vue'
import TutorBenchmark from '../components/TutorBenchmark.vue'
import TutorLiveEvaluation from '../components/TutorLiveEvaluation.vue'
const route=useRoute(),router=useRouter(),owner=user.value!.id
const sets=ref<SetSummary[]>([]),sessions=ref<TutorSummary[]>([]),config=ref<AIConfig>(),loading=ref(true),busy=ref(false),error=ref(''),listError=ref(''),historyError=ref(''),pending=ref<PendingTutorRequest|null>(null)
const setId=ref(String(route.query.setId||'')),goal=ref(''),mode=ref<TutorMode>('rule'),maxQuestions=ref(3)
let disposed=false,generation=0,historyGeneration=0
const active=()=>!disposed&&!sessionFrozen.value&&!identityChanging.value&&user.value?.id===owner
const selected=computed(()=>sets.value.find(s=>s.id===setId.value))
const limit=computed(()=>Math.min(10,selected.value?.questionCount||10))
const valid=computed(()=>!!selected.value&&selected.value.questionCount>0&&goal.value.trim().length>0&&goal.value.trim().length<=1000&&Number.isInteger(maxQuestions.value)&&maxQuestions.value>=1&&maxQuestions.value<=limit.value)
const flow=createTutorRequest(localStorage,`examhub:tutor:create:${owner}`,async operation=>{if(operation.kind!=='create')throw new Error('创建请求类型无效');return (await tutorApi.create(operation.body)).session},value=>pending.value=value,session=>{void router.push(`/tutor/${session.id}`)},active)
async function load(){
  const token=++generation;loading.value=true;listError.value=''
  const results=await Promise.allSettled([api.sets('mine'),api.sets('discover'),setId.value?api.set(setId.value):Promise.resolve(null),api.config()])
  if(!active()||token!==generation)return
  const found: SetSummary[]=[]
  for(const result of results.slice(0,3)){if(result.status==='fulfilled'&&result.value){const data=result.value;if('sets' in data)found.push(...data.sets);if('set' in data)found.push(data.set)}else if(result.status==='rejected')listError.value=message(result.reason)}
  sets.value=[...new Map(found.map(s=>[s.id,s])).values()]
  if(results[3].status==='fulfilled')config.value=results[3].value as AIConfig
  if(!setId.value&&sets.value.length)setId.value=sets.value[0].id
  maxQuestions.value=Math.max(1,Math.min(maxQuestions.value,limit.value));loading.value=false
}
async function loadHistory(){const token=++historyGeneration;historyError.value='';try{const data=await tutorApi.sessions();if(active()&&token===historyGeneration)sessions.value=data.sessions}catch(e){if(active()&&token===historyGeneration)historyError.value=message(e)}}
async function start(retry=false){
  if(busy.value||!active())return
  if(!retry&&!valid.value){error.value='请选择有题目的题集，填写目标，并确认题数范围';return}
  busy.value=true;error.value=''
  try{if(retry)await flow.retry();else await flow.submit({kind:'create',body:{setId:setId.value,goal:goal.value.trim(),mode:mode.value,maxQuestions:maxQuestions.value}})}catch(e){if(active())error.value=message(e)}finally{if(!disposed)busy.value=false}
}
function discard(){if(!window.confirm('保留已拒绝的请求记录并重新填写？旧记录可在当前浏览器中保留。'))return;try{flow.discard();error.value=''}catch(e){error.value=message(e)}}
const unregister=registerIdentityGuard(reason=>{if(reason==='confirm'&&busy.value){notify('创建请求正在确认，请稍后切换账户');return false}return true})
onMounted(()=>{try{flow.restore()}catch(e){error.value=message(e)}void load();void loadHistory()})
onBeforeUnmount(()=>{disposed=true;generation++;historyGeneration++;flow.dispose();unregister()})
</script>
<template><div class="page-container tutor-setup"><header class="page-heading"><div><h1>教学教练</h1><p>选定目标 逐题作答与反馈</p></div><RouterLink to="/library" class="button"><Icon name="library"/>查看题库</RouterLink></header>
<div class="tutor-setup-grid"><section class="surface tutor-config"><div class="section-head"><h2>学习目标</h2></div>
<div v-if="pending" class="tutor-recovery" role="status"><h3>{{pending.blocked?'上次请求已被拒绝':'有一份待确认的创建请求'}}</h3><p>保留原请求恢复，避免创建重复会话。恢复已接受的请求无需重新配置密钥。</p><p v-if="pending.error" class="error">{{pending.error}}</p><div class="row"><button v-if="!pending.blocked" class="button primary" :disabled="busy" @click="start(true)">恢复创建结果</button><button v-else class="button" :disabled="busy" @click="discard">保留记录并重新填写</button><button class="text-button" @click="downloadJSON(pending,'tutor-request.json')">导出请求记录</button></div></div>
<fieldset class="form-stack" :disabled="busy||!!pending"><label>学习题集<select v-model="setId" @change="maxQuestions=Math.max(1,Math.min(maxQuestions,limit))"><option value="" disabled>{{loading?'正在读取题集…':'请选择题集'}}</option><option v-for="item in sets" :key="item.id" :value="item.id" :disabled="!item.questionCount">{{item.title}} · {{item.questionCount}} 题</option></select></label><p v-if="selected" class="small muted">将保存版本 {{selected.version}} 的题目快照，后续题集改动不会改变本次学习</p><label>这次想解决什么<textarea v-model="goal" maxlength="1000" rows="3" placeholder="例如：理清概念差异，并能解释自己的选择理由"/></label><div class="tutor-modes" :data-mode="mode" role="group" aria-label="教练模式"><label class="tutor-mode-option" data-mode="rule" :class="{selected:mode==='rule'}"><input v-model="mode" type="radio" value="rule"/><span><strong>规则教练</strong><small>顺序练习与解析<br/>无需模型密钥</small></span></label><label class="tutor-mode-option" data-mode="agent" :class="{selected:mode==='agent'}"><input v-model="mode" type="radio" value="agent"/><span><strong>Agent 教练</strong><small>选工具并追问<br/>使用已配置模型</small></span></label></div><label>本次最多练习几题<input v-model.number="maxQuestions" type="number" min="1" :max="limit"/></label><Transition name="field"><p v-if="mode==='agent'" class="inline-note">{{config?.configured?`使用 ${config.model}，启动与恢复可能产生供应商费用`:'Agent 模式需要模型密钥；规则教练仍可使用'}} <RouterLink v-if="!config?.configured" to="/settings">配置模型</RouterLink></p></Transition><button class="button primary large" :disabled="!valid||busy||(mode==='agent'&&!config?.configured)" @click="start()">{{busy?'正在确认创建…':mode==='rule'?'开始规则教练':'启动 Agent · 调用模型'}}<Icon name="right"/></button></fieldset>
<p v-if="error&&error!==pending?.error" class="error" role="alert">{{error}}</p><p v-if="listError" class="error">{{listError}}<button class="text-button" @click="load">重读可访问题集</button></p><div v-if="!loading&&!sets.length" class="inline-note">还没有可练习题集。<RouterLink to="/discover">去发现题集</RouterLink>，或先创建自己的题集。</div></section>
<aside class="tutor-principles tutor-session-notes" aria-labelledby="tutor-session-notes-title"><div class="section-head"><h2 id="tutor-session-notes-title">会话说明</h2></div><div class="tutor-principle"><Icon name="check"/><div><h3>回答与追问</h3><p>每次提问都等待你的回答 简答与理由不自动判定掌握</p></div></div><div class="tutor-principle"><Icon name="document"/><div><h3>教材引用</h3><p>查阅学习记录 仅引用本次会话允许的摘录 引用与调用轨迹可查看和导出</p></div></div><div class="tutor-principle"><Icon name="lock"/><div><h3>暂停与恢复</h3><p>已完成步骤保存在会话中；暂停不会撤销已发送的模型请求</p></div></div></aside></div>
<section class="tutor-history"><div class="section-head"><h2>继续学习</h2><button class="text-button" @click="loadHistory"><Icon name="refresh"/>刷新</button></div><p v-if="historyError" class="error">{{historyError}}</p><div v-if="!sessions.length&&!historyError" class="empty-state compact"><Icon name="history"/><h3>暂无学习会话</h3><p>创建后可在这里返回会话，不会自动启动模型</p></div><RouterLink v-for="item in sessions" :key="item.id" :to="`/tutor/${item.id}`" class="history-row"><span class="set-symbol"><Icon :name="item.mode==='agent'?'ai':'book'"/></span><span class="history-title"><strong>{{item.setTitle}}</strong><span>{{tutorMode[item.mode]}} · {{date(item.updatedAt)}} · {{tutorStatus[item.status]}}</span></span><Icon name="right"/></RouterLink></section><TutorBenchmark/><TutorLiveEvaluation/></div></template>
