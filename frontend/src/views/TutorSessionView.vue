<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type AIConfig } from '../lib/api'
import { tutorApi, tutorMode, tutorStatus, tutorToolLabel, type TutorSession, type TutorCommand } from '../lib/tutor'
import { createTutorRequest, createTutorReader, type PendingTutorRequest } from '../lib/tutorRequests'
import { user, sessionFrozen, identityChanging, message, notify, registerIdentityGuard } from '../lib/state'
import { downloadJSON } from '../lib/documents'
import Icon from '../components/Icon.vue'
import TutorTranscript from '../components/TutorTranscript.vue'
const route=useRoute(),id=String(route.params.id),owner=user.value!.id
const session=ref<TutorSession>(),answer=ref(''),pendingRequest=ref<PendingTutorRequest|null>(null),busy=ref(false),loading=ref(true),error=ref(''),storageError=ref(''),config=ref<AIConfig>(),conflict=ref(false)
let disposed=false,timer:ReturnType<typeof setTimeout>|undefined,draftKey=''
const active=()=>!disposed&&!sessionFrozen.value&&!identityChanging.value&&user.value?.id===owner&&String(route.params.id)===id
const waiting=computed(()=>session.value?.status==='waiting'&&!!session.value.pending)
const canAnswer=computed(()=>waiting.value&&!session.value?.busy&&!busy.value&&!pendingRequest.value&&!!answer.value.trim()&&answer.value.trim().length<=6000)
const isSingle=computed(()=>session.value?.pending?.kind==='question'&&session.value.currentQuestion?.type==='single')
function saveDraft(){if(!draftKey)return;try{localStorage.setItem(draftKey,answer.value);storageError.value=''}catch{storageError.value='无法保存本地草稿，请先复制回答，避免离开后丢失'}}
watch(answer,saveDraft,{flush:'sync'})
function applySession(value:TutorSession){
  if(!active()||value.id!==id||(session.value&&value.version<session.value.version))return
  const nextKey=value.pending?`examhub:tutor:answer:${owner}:${id}:${value.turnId}`:''
  if(draftKey!==nextKey){saveDraft();draftKey=nextKey;try{answer.value=nextKey?localStorage.getItem(nextKey)||'':''}catch{answer.value='';storageError.value='无法读取本地草稿'}}
  session.value=value;loading.value=false
}
const reader=createTutorReader(async()=>(await tutorApi.session(id)).session,applySession,active)
const flow=createTutorRequest(localStorage,`examhub:tutor:command:${owner}:${id}`,async operation=>{if(operation.kind!=='command'||operation.sessionId!==id)throw new Error('会话请求不匹配');return (await tutorApi.command(id,operation.body)).session},value=>pendingRequest.value=value,applySession,active)
function schedule(){clearTimeout(timer);if(active()&&(session.value?.busy||session.value?.status==='running'))timer=setTimeout(()=>load(false),1300)}
async function load(manual=true){if(!active())return;if(manual)error.value='';try{await reader.read();if(active())schedule()}catch(e){if(active())error.value=message(e)}finally{if(active())loading.value=false}}
async function command(type:TutorCommand['type']){
  if(!session.value||busy.value||!active())return
  if(type==='answer'&&!canAnswer.value)return
  busy.value=true;error.value='';conflict.value=false;clearTimeout(timer);saveDraft()
  try{await flow.submit({kind:'command',sessionId:id,body:{version:session.value.version,type,...(type==='answer'?{turnId:session.value.turnId,answer:answer.value.trim()}:{})}})}catch(e){await handleError(e)}finally{if(!disposed){busy.value=false;schedule()}}
}
async function handleError(e:unknown){
  if(!active())return;error.value=message(e)
  const failure=e as {status?:number;code?:string}
  if(failure.status===409&&failure.code!=='session_changed'){conflict.value=true;await load(false)}
}
async function retry(){if(busy.value||!active())return;busy.value=true;error.value='';clearTimeout(timer);try{await flow.retry()}catch(e){await handleError(e)}finally{if(!disposed){busy.value=false;schedule()}}}
async function discard(){
  if(!window.confirm('保留这份已拒绝请求与原作答草稿，读取最新进度后重新操作？不会自动重新提交。'))return
  try{flow.discard();conflict.value=false;error.value='';await load()}catch(e){error.value=message(e)}
}
const unregister=registerIdentityGuard(reason=>{saveDraft();if(reason==='confirm'&&busy.value){notify('教学操作正在确认，请稍后切换账户');return false}return !storageError.value})
watch(sessionFrozen,frozen=>{if(frozen){clearTimeout(timer);saveDraft()}else if(active())void load(false)})
onMounted(()=>{try{flow.restore()}catch(e){error.value=message(e)}void load();void api.config().then(value=>{if(active())config.value=value}).catch(()=>{})})
onBeforeUnmount(()=>{saveDraft();disposed=true;clearTimeout(timer);reader.dispose();flow.dispose();unregister()})
</script>
<template><div class="page-container tutor-session"><RouterLink to="/tutor" class="back-link"><Icon name="left"/>返回教学教练</RouterLink><div v-if="loading&&!session" class="loading" role="status">正在读取已保存的教学进度…</div><div v-else-if="!session" class="empty-state"><Icon name="lock"/><h2>暂时无法打开这段学习</h2><p>{{error||'会话不存在或不属于当前账户'}}</p><button class="button" @click="load()">重新读取</button></div><template v-if="session"><header class="page-heading"><div><span class="topic-label">{{tutorMode[session.mode]}} · 题集版本 {{session.setVersion}}</span><h1>{{session.setTitle}}</h1><p>{{session.goal}}</p></div><button class="button" @click="downloadJSON(session,`tutor-${session.id}.json`)"><Icon name="download"/>导出会话</button></header>
<div class="tutor-session-grid"><div class="tutor-main"><section class="tutor-current surface"><div class="section-head"><span class="tutor-state"><span :class="{working:session.busy}"/>{{tutorStatus[session.status]}}</span><span class="small muted">最多 {{session.maxQuestions}} 题</span></div>
<div v-if="pendingRequest" class="tutor-recovery" role="status"><h3>{{pendingRequest.blocked?'请求未执行，请核对最新进度':'有一条待确认的教学操作'}}</h3><p>{{pendingRequest.blocked?'原作答保留，不会自动重答。请阅读最新问题后再决定。':'服务可能已经接受，使用原请求恢复，不会重复提交同一回答。'}}</p><p v-if="pendingRequest.error" class="error">{{pendingRequest.error}}</p><div class="row"><button v-if="!pendingRequest.blocked" class="button primary" :disabled="busy" @click="retry">恢复原请求结果</button><button v-else class="button" :disabled="busy" @click="discard">保留旧请求并按最新状态继续</button><button class="text-button" @click="downloadJSON(pendingRequest,'tutor-pending-command.json')">导出请求记录</button></div></div>
<Transition name="page" mode="out-in"><div v-if="session.pending" :key="session.turnId" class="tutor-question"><span class="type-label">{{session.pending.kind==='followup'?'再想一步 · 说明你的理由':isSingle?'单选题':'简答题 · 不自动判分'}}</span><h2>{{session.pending.prompt}}</h2><p v-if="session.pending.kind==='followup'&&session.currentQuestion" class="small muted">原题：{{session.currentQuestion.prompt}}</p><fieldset :disabled="!waiting||session.busy||busy||!!pendingRequest"><div v-if="isSingle" class="practice-options"><label v-for="(option,index) in session.currentQuestion?.options" :key="index" :class="{chosen:answer===option}"><input v-model="answer" type="radio" :name="`tutor-${session.turnId}`" :value="option"/><span class="option-letter">{{String.fromCharCode(65+index)}}</span><span>{{option}}</span><Icon v-if="answer===option" name="check"/></label></div><label v-else class="short-answer">{{session.pending.kind==='followup'?'你的理由':'你的回答'}}<textarea v-model="answer" maxlength="6000" rows="6" placeholder="用自己的话写下思路…"/></label></fieldset><div class="tutor-submit"><span class="small muted">草稿保存在当前账户与当前问题下</span><button class="button primary" :disabled="!canAnswer" @click="command('answer')">{{busy?'正在确认…':session.pending.kind==='followup'?'提交理由':'提交回答'}}<Icon name="right"/></button></div></div><div v-else-if="session.status==='completed'" key="complete" class="tutor-finished"><Icon name="check"/><h2>这一段学习已完成</h2><p>回看自己的回答与教练反馈，核对引用，再决定下一步。</p><RouterLink :to="`/tutor?setId=${session.setId}`" class="button primary">设置下一次学习目标</RouterLink></div><div v-else key="processing" class="tutor-waiting"><Icon :name="session.status==='paused'?'history':'book'"/><h2>{{session.status==='paused'?'在这里停一下也没关系':'教练正在准备下一步'}}</h2><p>{{session.status==='paused'?'已保存的回答与工具结果都还在，继续需要你明确点击。':'工具执行结果逐步保存。下一道题或追问出现后，教练会等待你的回答。'}}</p></div></Transition>
<p v-if="session.error" class="error" role="alert">{{session.error}}</p><p v-if="error&&error!==pendingRequest?.error&&error!==session.error" class="error" role="alert">{{error}}</p><p v-if="conflict" class="inline-note">进度已更新，当前显示最新可读取状态。原请求不会自动重放。</p><p v-if="storageError" class="error" role="alert">{{storageError}}</p><div class="tutor-controls"><button v-if="session.status==='paused'" class="button primary" :disabled="busy||session.busy||!!pendingRequest" @click="command('resume')">{{session.mode==='agent'?'恢复 Agent · 可能调用模型':'继续规则教练'}}</button><button v-else-if="session.status!=='completed'" class="button" :disabled="busy||!!pendingRequest" @click="command('stop')">暂停教学</button><button class="text-button" :disabled="busy" @click="load()"><Icon name="refresh"/>读取最新进度</button></div><p v-if="session.busy" class="small muted">后台请求仍在收尾，完成前不能再次作答或恢复；暂停不会撤销已发送的调用。</p><p v-if="session.mode==='agent'" class="small muted">Agent 的提交与恢复可能调用模型并产生费用。{{config?.configured?'': '当前未确认模型密钥；读取已有进度和重试已接受的请求不受影响。'}} <RouterLink v-if="!config?.configured" to="/settings">模型设置</RouterLink></p></section>
<TutorTranscript :events="session.events"/></div><aside class="tutor-context"><section class="surface tutor-facts"><h3>本次学习事实</h3><dl><div><dt>已答题目</dt><dd>{{session.summary.answered}} / {{session.maxQuestions}}</dd></div><div><dt>单选答对</dt><dd>{{session.summary.objectiveTotal?`${session.summary.correct} / ${session.summary.objectiveTotal}`:'暂无单选作答'}}</dd></div><div><dt>已答追问</dt><dd>{{session.summary.followups}}</dd></div></dl><p class="small muted">简答与理由不计入自动得分<br/>反馈不代表已经掌握</p></section><section class="surface tutor-budget"><h3>{{session.mode==='rule'?'规则运行':'模型调用预算'}}</h3><dl><div><dt>实际模型调用</dt><dd>{{session.modelCalls}}<span v-if="session.mode==='agent'"> / {{session.budget.maxModelCalls}}</span></dd></div><div v-if="session.mode==='agent'"><dt>剩余调用预算</dt><dd>{{session.budget.remainingModelCalls}}</dd></div><div><dt>累计处理耗时</dt><dd>{{session.elapsedMs==null||session.timingIncomplete?'计时不完整':`${(session.elapsedMs/1000).toFixed(2)} 秒`}}</dd></div></dl><p class="small muted">{{session.mode==='rule'?`每轮最多 ${session.budget.maxRuleStepsPerTurn} 个规则步骤，不调用模型`:`每轮最多 ${session.budget.maxModelCallsPerTurn} 次模型调用`}}。耗时不含等待你作答的时间。</p></section><section class="surface tutor-trace"><div class="section-head"><h3>工具轨迹</h3><span class="badge">{{session.trace.length}} 步</span></div><p class="small muted">展示执行摘要，不展示模型内部推理</p><p v-if="!session.trace.length" class="small muted">尚无已保存的工具执行</p><details v-for="(step,index) in session.trace" :key="index"><summary><span>{{index+1}} · {{tutorToolLabel(step.tool)}}</span><Icon :name="step.status==='error'?'warning':'check'"/></summary><p>{{step.message}}</p><p v-if="step.argsSummary" class="muted">{{step.argsSummary}}</p><p v-if="step.resultSummary" class="muted">{{step.resultSummary}}</p><p v-if="step.elapsedMs!==undefined" class="small muted">{{step.elapsedMs}} 毫秒</p></details></section></aside></div></template></div></template>
