<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { api, type AIConfig } from '../lib/api'
import { tutorLiveApi, createLiveStartRequest, liveStartValid, liveStatus, liveDimensions, type LiveDataset, type LiveEvaluation, type LiveBlindPackage, type LiveDimension, type LiveReviewInput, type PendingLiveStart } from '../lib/tutorLive'
import { user, sessionFrozen, identityChanging, registerIdentityGuard, notify, message, date } from '../lib/state'
import { downloadJSON } from '../lib/documents'
import Icon from './Icon.vue'

const owner=user.value!.id
const dataset=ref<LiveDataset>(),config=ref<AIConfig>(),caseIds=ref<string[]>([]),repeats=ref(1),maxCalls=ref(10),paidConfirmed=ref(false)
const pending=ref<PendingLiveStart|null>(null),busy=ref(false),loading=ref(true),error=ref(''),loadError=ref(''),historyError=ref('')
const history=shallowRef<LiveEvaluation[]>([]),evaluation=shallowRef<LiveEvaluation>(),selectedId=ref(''),blindPackage=shallowRef<LiveBlindPackage>(),blindLoading=ref(false)
const reviewId=ref(''),reviewer=ref(''),reviewerType=ref<LiveReviewInput['reviewerType']>('human'),reviewVersion=ref<number|null>(null),reviewConflict=ref(false)
const scores=ref<Record<LiveDimension,number|null>>({accuracy:null,grounding:null,diagnosis:null,actionability:null})
const notes=ref<Record<LiveDimension,string>>({accuracy:'',grounding:'',diagnosis:'',actionability:''})
let disposed=false,epoch=0,viewGeneration=0,loadGeneration=0,historyGeneration=0,detailGeneration=0,blindGeneration=0,timer:ReturnType<typeof setTimeout>|undefined
const active=()=>!disposed&&!sessionFrozen.value&&!identityChanging.value&&user.value?.id===owner
const processing=(value:LiveEvaluation)=>value.busy===true||value.status==='queued'||value.status==='running'
const running=computed(()=>!!evaluation.value&&processing(evaluation.value))
const plannedTrials=computed(()=>caseIds.value.length*repeats.value*2)
const canStart=computed(()=>active()&&!loading.value&&!busy.value&&!pending.value&&config.value?.configured===true&&paidConfirmed.value&&liveStartValid({caseIds:caseIds.value,repeats:repeats.value,maxCalls:maxCalls.value})&&caseIds.value.every(id=>dataset.value?.cases.some(item=>item.id===id))&&!history.value.some(processing)&&!running.value)
const reviewNotes=computed(()=>liveDimensions.map(d=>`${d.label}：${notes.value[d.key].trim()}`).join('\n'))
const canReview=computed(()=>active()&&!busy.value&&!running.value&&!reviewConflict.value&&!!evaluation.value&&reviewVersion.value!==null&&!!reviewId.value&&!!reviewer.value.trim()&&reviewer.value.trim().length<=80&&['human','ai-assisted'].includes(reviewerType.value)&&liveDimensions.every(d=>[0,1,2].includes(scores.value[d.key]??-1)&&!!notes.value[d.key].trim())&&reviewNotes.value.length<=3000)

function invalidate(){epoch++;loadGeneration++;historyGeneration++;detailGeneration++;blindGeneration++;blindLoading.value=false;clearTimeout(timer)}
function schedule(){clearTimeout(timer);if(active()&&running.value)timer=setTimeout(()=>void refresh(false),1500)}
function applyEvaluation(value:LiveEvaluation){
  if(!active()||value.id!==selectedId.value||(evaluation.value&&value.version<evaluation.value.version))return
  evaluation.value=value
  history.value=[value,...history.value.filter(item=>item.id!==value.id)]
}
function received(value:LiveEvaluation){
  viewGeneration++;detailGeneration++;blindGeneration++;blindLoading.value=false;selectedId.value=value.id;evaluation.value=undefined;blindPackage.value=undefined;reviewId.value=''
  applyEvaluation(value);paidConfirmed.value=false;schedule()
}
const flow=createLiveStartRequest(localStorage,`examhub:tutor:live-start:${owner}`,async body=>{
  const token=epoch,data=await tutorLiveApi.create(body)
  if(!active()||token!==epoch)throw Object.assign(new Error('账户状态已变化，原请求记录已保留'),{code:'session_changed'})
  return data.evaluation
},value=>pending.value=value,received,active)

async function load(){
  if(!active())return
  const token=++loadGeneration;loading.value=true;loadError.value='';config.value=undefined
  const results=await Promise.allSettled([tutorLiveApi.dataset(),api.config()])
  if(!active()||token!==loadGeneration)return
  if(results[0].status==='fulfilled'){
    dataset.value=results[0].value.dataset
    caseIds.value=caseIds.value.filter(id=>dataset.value!.cases.some(item=>item.id===id))
    if(!caseIds.value.length)caseIds.value=dataset.value.cases.map(item=>item.id)
  }else{dataset.value=undefined;loadError.value=message(results[0].reason)}
  if(results[1].status==='fulfilled')config.value=results[1].value
  else loadError.value=[loadError.value,message(results[1].reason)].filter(Boolean).join('；')
  loading.value=false
}
async function loadHistory(){
  if(!active())return
  const token=++historyGeneration;historyError.value=''
  try{
    const data=await tutorLiveApi.evaluations()
    if(!active()||token!==historyGeneration)return
    history.value=data.evaluations.map(item=>evaluation.value?.id===item.id&&evaluation.value.version>item.version?evaluation.value:item)
    if(!selectedId.value&&history.value.length)await selectEvaluation(history.value[0].id)
  }catch(e){if(active()&&token===historyGeneration)historyError.value=message(e)}
}
async function selectEvaluation(id:string){
  if(!active()||busy.value)return
  if(selectedId.value===id&&evaluation.value){await refresh();return}
  clearTimeout(timer);viewGeneration++;detailGeneration++;blindGeneration++;blindLoading.value=false;selectedId.value=id;evaluation.value=undefined;blindPackage.value=undefined;reviewId.value='';reviewConflict.value=false;error.value=''
  await refresh()
}
async function refresh(manual=true){
  if(!active()||!selectedId.value)return
  clearTimeout(timer)
  const token=++detailGeneration,id=selectedId.value
  if(manual)error.value=''
  try{
    const data=await tutorLiveApi.evaluation(id)
    if(!active()||token!==detailGeneration||id!==selectedId.value)return
    applyEvaluation(data.evaluation);schedule()
  }catch(e){if(active()&&token===detailGeneration&&id===selectedId.value)error.value=message(e)}
}
async function start(retry=false){
  if(!active()||busy.value||(!retry&&!canStart.value))return
  const token=epoch;busy.value=true;error.value=''
  try{if(retry)await flow.retry();else await flow.submit({caseIds:caseIds.value,repeats:repeats.value,maxCalls:maxCalls.value})}
  catch(e){if(active()&&token===epoch)error.value=message(e)}
  finally{if(!disposed)busy.value=false}
}
function discard(){if(!active()||busy.value)return;try{flow.discard();error.value='';paidConfirmed.value=false}catch(e){error.value=message(e)}}
async function cancel(){
  if(!active()||busy.value||!evaluation.value||!['queued','running'].includes(evaluation.value.status))return
  const id=selectedId.value,token=epoch,view=viewGeneration;busy.value=true;error.value='';detailGeneration++;clearTimeout(timer)
  try{const data=await tutorLiveApi.cancel(id);if(active()&&token===epoch&&view===viewGeneration)applyEvaluation(data.evaluation)}
  catch(e){if(active()&&token===epoch&&view===viewGeneration)error.value=message(e)}
  finally{if(!disposed){busy.value=false;if(token===epoch&&view===viewGeneration)schedule()}}
}
async function loadBlind(){
  if(!active()||!evaluation.value||running.value)return
  const id=selectedId.value,token=++blindGeneration,view=viewGeneration;blindLoading.value=true;error.value=''
  try{
    const data=await tutorLiveApi.blind(id)
    if(!active()||token!==blindGeneration||view!==viewGeneration)return
    blindPackage.value=data.package;return data.package
  }catch(e){if(active()&&token===blindGeneration&&view===viewGeneration)error.value=message(e)}
  finally{if(!disposed&&token===blindGeneration)blindLoading.value=false}
}
async function downloadBlind(){const token=epoch,view=viewGeneration,value=await loadBlind();if(value&&active()&&token===epoch&&view===viewGeneration)downloadJSON(value,'tutor-blind-review.json')}
function downloadReport(){if(active()&&evaluation.value)downloadJSON(evaluation.value,'tutor-live-evaluation.json')}
function beginReview(id:string){
  if(!active()||busy.value||running.value||!evaluation.value||!blindPackage.value?.items.some(item=>item.blindId===id))return
  reviewId.value=id;reviewVersion.value=evaluation.value.version;reviewConflict.value=false
  scores.value={accuracy:null,grounding:null,diagnosis:null,actionability:null};notes.value={accuracy:'',grounding:'',diagnosis:'',actionability:''}
}
function rebaseReview(){if(active()&&!busy.value&&!running.value&&evaluation.value){reviewVersion.value=evaluation.value.version;reviewConflict.value=false;error.value=''}}
async function saveReview(){
  if(!canReview.value)return
  const id=selectedId.value,token=epoch,view=viewGeneration
  const body:LiveReviewInput={version:reviewVersion.value!,reviewer:reviewer.value.trim(),reviewerType:reviewerType.value,scores:{...scores.value} as Record<LiveDimension,number>,notes:reviewNotes.value}
  busy.value=true;error.value='';detailGeneration++;clearTimeout(timer)
  try{
    const data=await tutorLiveApi.review(id,reviewId.value,body)
    if(!active()||token!==epoch||view!==viewGeneration)return
    applyEvaluation(data.evaluation);reviewId.value='';notify('复核结果已保存')
  }catch(e){
    if(active()&&token===epoch&&view===viewGeneration){
      error.value=message(e)
      if((e as {status?:number;code?:string}).status===409&&(e as {code?:string}).code!=='session_changed'){reviewConflict.value=true;await refresh(false)}
    }
  }finally{if(!disposed)busy.value=false}
}
const unregister=registerIdentityGuard(reason=>{
  if(reason==='preserve')invalidate()
  if(reason==='confirm'&&busy.value){notify('评测操作正在确认，请等待结果保存后切换账户');return false}
  return true
})
watch(()=>[sessionFrozen.value,identityChanging.value,user.value?.id],()=>{if(!active())invalidate();else{void load();void loadHistory();if(selectedId.value)void refresh(false)}},{flush:'sync'})
onMounted(()=>{try{flow.restore()}catch(e){error.value=message(e)}void load();void loadHistory()})
onBeforeUnmount(()=>{disposed=true;invalidate();flow.dispose();unregister()})
</script>

<template>
  <section class="surface tutor-benchmark tutor-live" aria-label="真实模型教学评测">
    <div class="section-head"><div><h2>真实模型教学评测</h2><p class="muted small">固定学生回答，比较规则与模型的实际教学行为</p></div><Icon name="ai"/></div>
    <p class="muted">固定学生不是真人，也不模拟学习。完成率、答题正确率和工具调用率不代表教学质量或学习收益。人工复核单独记录，不计入行为通过率。</p>

    <Transition name="fade"><div v-if="pending" class="tutor-recovery" role="status">
      <h3>{{pending.blocked?'上次启动请求已被拒绝':'有一份结果待确认的启动请求'}}</h3>
      <p>原请求包含 {{pending.body.caseIds.length}} 个场景、每种策略重复 {{pending.body.repeats}} 次、最多 {{pending.body.maxCalls}} 次付费调用。重试使用同一请求编号和完整参数；若原请求尚未被接受，此次重试会启动付费作业。</p>
      <p v-if="pending.error" class="error">{{pending.error}}</p>
      <div class="row"><button v-if="!pending.blocked" class="button primary" :disabled="busy" @click="start(true)">使用原请求重试 · 可能付费</button><button v-else class="button" :disabled="busy" @click="discard">归档拒绝记录并重新填写</button></div>
    </div></Transition>
    <fieldset class="form-stack live-form" :disabled="busy||!!pending||loading">
      <legend>选择原创场景</legend>
      <div class="live-cases"><label v-for="item in dataset?.cases" :key="item.id" :class="{selected:caseIds.includes(item.id)}"><input v-model="caseIds" type="checkbox" :value="item.id"/><span><strong>{{item.title}}</strong><small>{{item.goal}}</small></span></label></div>
      <div class="form-columns"><label>每个场景、每种策略重复次数<input v-model.number="repeats" type="number" min="1" max="3"/></label><label>本次模型调用预算<input v-model.number="maxCalls" type="number" min="1" max="20"/></label></div>
      <p class="small muted">共 {{plannedTrials}} 个 trial，规则与模型各 {{plannedTrials/2}} 个；每个模型 trial 最多 10 次调用、每个 trial 最多 40 步。预算不足时保留未运行项，不会自动补跑。</p>
      <p class="inline-note"><Icon name="warning"/>{{config?.configured?`使用 ${config.model}，最多 ${maxCalls} 次模型调用可能产生供应商费用。实际 token 缺失时保持未知，不推算金额。`:'需要已保存的模型配置才能启动。规则对比随本次作业一同运行。'}}<RouterLink v-if="config&&!config.configured" to="/settings">前往设置</RouterLink></p>
      <label class="live-consent"><input v-model="paidConfirmed" type="checkbox"/>我确认本次调用预算与可能产生的供应商费用</label>
      <button class="button primary" :disabled="!canStart" @click="start()"><Icon name="ai"/>{{busy?'正在确认操作…':'开始真实模型评测 · 可能付费'}}</button>
    </fieldset>
    <p v-if="loading" class="small muted" role="status">正在读取数据集与模型配置…</p>
    <p v-if="loadError" class="error" role="alert">{{loadError}}<button class="text-button" @click="load">重新读取数据集与配置</button></p>
    <p v-if="error&&error!==pending?.error" class="error" role="alert">{{error}}</p>
    <details v-if="dataset"><summary>数据集版本与边界</summary><p>{{dataset.id}} · {{dataset.version}}</p><p class="hash-line">SHA256 {{dataset.hash}}</p><ul class="report-limits"><li v-for="limit in dataset.limitations" :key="limit">{{limit}}</li></ul></details>

    <div class="section-head live-history-heading"><h3>评测作业</h3><button class="text-button" :disabled="busy" @click="loadHistory"><Icon name="refresh"/>读取历史</button></div>
    <p class="small muted">刷新只读取已有作业，不会自动创建或重新启动付费请求</p>
    <p v-if="historyError" class="error" role="alert">{{historyError}}</p>
    <label v-if="history.length" class="live-history-select">查看已有作业<select :value="selectedId" :disabled="busy" @change="selectEvaluation(($event.target as HTMLSelectElement).value)"><option v-for="item in history" :key="item.id" :value="item.id">{{date(item.createdAt)}} · {{item.model}} · {{liveStatus[item.status]}} · {{item.id}}</option></select></label>
    <p v-else class="small muted">暂无已读取的评测记录</p>

    <Transition name="fade" mode="out-in"><div v-if="evaluation" :key="evaluation.id" class="live-result">
      <div class="section-head"><h3>{{liveStatus[evaluation.status]}}<span v-if="evaluation.busy" class="small muted"> · 正在保存响应</span></h3><div class="row"><button class="text-button" :disabled="busy" @click="refresh()"><Icon name="refresh"/>读取进度</button><button v-if="['queued','running'].includes(evaluation.status)" class="button danger" :disabled="busy" @click="cancel">取消作业</button></div></div>
      <p class="small muted" aria-live="polite">已计入调用预算 {{evaluation.modelCalls}} / {{evaluation.maxCalls}} · {{evaluation.model}} · {{evaluation.provider}} · 版本 {{evaluation.version}}</p>
      <p class="small muted">计数包含请求发送前预留；中断时不等于供应商计费次数，usage 为实际返回</p>
      <p v-if="evaluation.busy&&evaluation.status==='cancelled'" class="inline-note">取消已记录，正在等待已发送请求返回并保存。该请求仍可能计费，收尾后才能开始新作业或保存人工复核。</p>
      <p v-if="evaluation.error" class="error">{{evaluation.error}}</p>
      <p class="small muted">作业完成表示执行已结束。每条 trial 的失败、未运行、预算耗尽和中断均保留在总数中，不会自动付费重跑。</p>
      <p v-if="evaluation.report.graderVersion==='live-behavior-v1'" class="inline-note">历史判据 v1 的动作检查还要求正常结束，预算耗尽也记为未通过；原始结果保留，与新版分数不能直接比较</p>
      <div class="benchmark-strategies tutor-benchmark-strategies">
        <article v-for="strategy in (['rule','agent'] as const)" :key="strategy">
          <h3>{{strategy==='rule'?'规则教练':'真实模型教练'}}</h3>
          <div class="quality-summary"><span>行为通过 {{evaluation.report.summary[strategy].passed}} / {{evaluation.report.summary[strategy].trials}}</span><span>完成 {{evaluation.report.summary[strategy].completed}} / {{evaluation.report.summary[strategy].trials}}</span></div>
          <p class="small muted">检查通过 {{evaluation.report.summary[strategy].passedChecks}} / {{evaluation.report.summary[strategy].checks}} · 模型调用 {{evaluation.report.summary[strategy].modelCalls}}</p>
          <details v-for="trial in evaluation.report.trials.filter(t=>t.strategy===strategy)" :key="trial.id">
            <summary>{{trial.title}} · 第 {{trial.repeat}} 次 · {{liveStatus[trial.status]}}</summary>
            <p v-if="trial.error" class="error">{{trial.error}}</p>
            <p class="small muted">模型调用 {{trial.modelCalls}} · {{trial.elapsedMs==null?'耗时未知':`${trial.elapsedMs} 毫秒`}}</p>
            <p class="small muted">{{trial.usage?`实际 token：输入 ${trial.usage.prompt_tokens}，输出 ${trial.usage.completion_tokens}，总计 ${trial.usage.total_tokens}`:trial.strategy==='rule'?'规则教练不调用模型 · token 不适用':'usage 未返回，token 用量未知'}}</p>
            <ul class="tutor-benchmark-checks"><li v-for="check in trial.checks" :key="check.code"><strong><Icon :name="check.passed?'check':'warning'"/>{{check.message}} · {{check.passed?'通过':'未通过'}}</strong></li></ul>
            <p v-if="!trial.review" class="small muted">尚未人工复核 · 教学质量评分为空</p>
            <details v-else><summary>已保存的复核</summary><p>{{trial.review.reviewer}} · {{trial.review.reviewerType==='human'?'人工':'AI 辅助复核 · 非独立人工评分'}} · {{trial.review.updatedAt}}</p><p v-for="dimension in liveDimensions" :key="dimension.key">{{dimension.label}} {{trial.review.scores[dimension.key]}} / 2</p><p>{{trial.review.notes}}</p></details>
            <details><summary>固定回答、反馈与教材快照</summary><pre>{{JSON.stringify(trial.session,null,2)}}</pre></details>
            <details><summary>请求消息、原始 content 与工具结果 · {{trial.steps.length}} 步</summary><pre>{{JSON.stringify(trial.steps,null,2)}}</pre></details>
          </details>
        </article>
      </div>
      <ul class="report-limits"><li v-for="limit in evaluation.report.limitations" :key="limit">{{limit}}</li></ul>
      <div class="live-exports row"><button class="text-button" @click="downloadReport"><Icon name="download"/>下载实际报告 JSON</button><button class="text-button" :disabled="running||blindLoading" @click="downloadBlind"><Icon name="download"/>下载遮蔽复核包</button><button class="text-button" :disabled="running||blindLoading" @click="loadBlind">{{blindLoading?'正在读取复核包…':'打开人工复核'}}</button></div>
      <details><summary>完整原始 JSON 与可复现参数</summary><p>数据集 {{evaluation.report.datasetId}} · {{evaluation.report.datasetVersion}}</p><p class="hash-line">数据集 SHA256 {{evaluation.report.datasetHash}}<br/>提示 SHA256 {{evaluation.report.promptHash}}</p><p>行为判据 {{evaluation.report.graderVersion||'未记录'}}</p><p class="small muted">比较时请使用相同行为判据版本，历史计数保留原报告结果</p><pre>{{JSON.stringify(evaluation,null,2)}}</pre></details>

      <Transition name="fade"><section v-if="blindPackage" class="live-review" aria-label="人工教学质量复核">
        <h3>人工教学质量复核</h3><p class="muted small">请逐项阅读题目、教材、固定回答与反馈再评分。遮蔽包移除策略与模型字段并打乱顺序，文风仍可能暴露来源，不能保证正式双盲。这里不会调用模型裁判。</p>
        <details><summary>服务端评分量表</summary><pre>{{JSON.stringify(blindPackage.rubric,null,2)}}</pre></details>
        <details v-for="item in blindPackage.items" :key="item.blindId"><summary>{{item.caseTitle}} · {{item.blindId}}</summary><p>{{item.goal}}</p><h4>题目与教材</h4><pre>{{JSON.stringify(item.questions,null,2)}}</pre><h4>固定回答</h4><pre>{{JSON.stringify(item.answers,null,2)}}</pre><h4>反馈与追问</h4><pre>{{JSON.stringify(item.events,null,2)}}</pre><button class="button" :disabled="busy||running" @click="beginReview(item.blindId)">复核此条</button></details>
        <Transition name="fade"><form v-if="reviewId" class="form-stack live-review-form" @submit.prevent="saveReview">
          <p class="small muted">当前复核 {{reviewId}} · 编辑基于版本 {{reviewVersion}}</p>
          <fieldset class="form-stack" :disabled="busy||running"><div class="form-columns"><label>复核者<input v-model="reviewer" maxlength="80" required autocomplete="off"/></label><label>复核方式<select v-model="reviewerType"><option value="human">人工 · 独立阅读评分</option><option value="ai-assisted">AI 辅助复核 · 非独立人工评分</option></select></label></div>
            <div v-for="dimension in liveDimensions" :key="dimension.key" class="live-dimension"><label>{{dimension.label}} · 0–2 分<select v-model="scores[dimension.key]" required><option :value="null" disabled>请实际阅读后评分</option><option :value="0">0</option><option :value="1">1</option><option :value="2">2</option></select></label><label>{{dimension.label}}的评分依据<textarea v-model="notes[dimension.key]" rows="2" maxlength="700" required/></label></div>
          </fieldset>
          <p v-if="reviewConflict" class="error" role="alert">版本已变化，草稿已保留。请核对最新报告后再次确认版本，不会自动重交。<button type="button" class="text-button" :disabled="busy||running" @click="rebaseReview">已核对最新报告，使用版本 {{evaluation.version}}</button></p>
          <button type="submit" class="button primary" :disabled="!canReview">保存人工复核 · 不调用模型</button>
        </form></Transition>
      </section></Transition>
    </div></Transition>
  </section>
</template>

<style scoped>
.tutor-live{min-width:0;animation:reveal .22s ease}.tutor-live fieldset{border:0;padding:0;margin:0;min-width:0}.live-form{margin:24px 0!important}.live-form legend{font-size:13px;font-weight:600;margin-bottom:12px}.live-cases{display:grid;grid-template-columns:1fr 1fr;gap:12px}.live-cases label{flex-direction:row;align-items:flex-start;gap:10px;padding:15px;border:1px solid var(--line);border-radius:9px;transition:background .2s,border-color .2s,transform .2s}.live-cases label:hover{transform:translateY(-1px)}.live-cases label.selected{background:#eef3ff;border-color:#87a4f2}.live-cases input{margin-top:4px}.live-cases small{display:block;margin-top:7px;color:var(--muted);font-weight:400;line-height:1.8}.live-consent{flex-direction:row;align-items:flex-start;gap:10px}.live-consent input{margin-top:2px}.live-form>.button{align-self:flex-start}.live-form .inline-note{margin:0;flex-wrap:wrap}.live-history-heading{border-top:1px solid var(--line);padding-top:24px;margin-top:25px;margin-bottom:8px}.live-history-select{margin:16px 0 24px}.live-history-select select{max-width:100%}.live-result{margin-top:24px;min-width:0}.live-result>.section-head .row,.live-exports{flex-wrap:wrap}.live-exports{gap:16px;margin:23px 0}.live-review{border-top:1px solid var(--line);padding-top:24px;margin-top:24px}.live-review h4{font-size:12px;margin-bottom:5px}.live-review-form{margin:24px 0}.live-dimension{display:grid;grid-template-columns:minmax(120px,1fr) minmax(0,2fr);gap:16px}.live-dimension textarea{width:100%}.live-result .section-head{flex-wrap:wrap}.live-result details,.live-result article,.live-review{overflow-wrap:anywhere;transition:opacity .2s,background .2s}.live-result pre{text-align:left}.live-review-form>.button{align-self:flex-start}
@media(max-width:760px){.live-cases,.live-dimension{grid-template-columns:1fr}.live-form>.button,.live-review-form>.button{width:100%;white-space:normal}.live-result>.section-head{align-items:flex-start;gap:10px}.live-history-select select{font-size:12px}.live-exports{align-items:flex-start;flex-direction:column}}
</style>
