import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { ref, nextTick } from 'vue'
import { script, storage, deferred, renderView } from './harness.mjs'

const originalStorage=globalThis.localStorage
afterEach(()=>{globalThis.localStorage=originalStorage})
const helpers=await script('lib/tutorLive.ts',{request:()=>{}},['createLiveStartRequest','liveStartValid','liveStatus','liveDimensions'])
const dataset={id:'original',version:'1',hash:'data-hash',cases:[{id:'confusion',title:'概念混淆',goal:'诊断混淆'},{id:'reason',title:'理由追问',goal:'核对理由'}],limitations:['固定学生不模拟学习']}
const trial={id:'trial-1',blindId:'blind-one',caseId:'confusion',title:'概念混淆',strategy:'agent',repeat:1,status:'failed',error:'供应商失败',modelCalls:1,elapsedMs:null,usage:null,steps:[],session:null,checks:[{code:'feedback',message:'产生反馈',passed:false}],review:null}
const evaluation={id:'job-A',version:3,status:'failed',createdAt:'2026-10-20T00:00:00Z',updatedAt:'2026-10-20T00:00:01Z',model:'actual-model',provider:'provider',datasetHash:'data-hash',promptHash:'prompt-hash',maxCalls:8,modelCalls:1,error:'供应商失败',report:{kind:'live-tutor-evaluation',datasetId:'original',datasetVersion:'1',datasetHash:'data-hash',promptHash:'prompt-hash',parameters:{temperature:0.4},learner:'fixed-script',trials:[trial,{...trial,id:'trial-2',blindId:'blind-two',status:'budget',modelCalls:0,error:null}],summary:{rule:{trials:2,completed:2,passed:2,checks:2,passedChecks:2,modelCalls:0},agent:{trials:2,completed:0,passed:0,checks:2,passedChecks:0,modelCalls:1}},limitations:['行为通过不代表学习收益'],rubric:{accuracy:'事实正确'}}}
const blindPackage={kind:'blind-review',version:1,datasetHash:'data-hash',rubric:{accuracy:'事实正确'},items:[{blindId:'blind-one',caseTitle:'概念混淆',goal:'诊断混淆',questions:[{prompt:'题目',source:'教材摘录'}],answers:[{userAnswer:'固定回答'}],events:[{type:'feedback',message:'需要核对证据'}]}]}
const names=['dataset','config','caseIds','repeats','maxCalls','paidConfirmed','pending','busy','loading','error','loadError','historyError','history','evaluation','selectedId','blindPackage','blindLoading','reviewId','reviewer','reviewerType','scores','notes','reviewVersion','reviewConflict','canStart','canReview','running','plannedTrials','flow','load','loadHistory','selectEvaluation','refresh','start','discard','cancel','loadBlind','downloadBlind','downloadReport','beginReview','saveReview','rebaseReview','liveStatus','liveDimensions']
function env(overrides={}){
  globalThis.localStorage=storage()
  const timers=new Map(),downloads=[];let mounted,unmounted,guard,nextTimer=0
  const bindings={...helpers,user:ref({id:'owner'}),sessionFrozen:ref(false),identityChanging:ref(false),message:e=>e.message,notify:()=>{},date:x=>x,
    api:{config:async()=>({configured:true,model:'configured-model',baseUrl:'unused'})},
    tutorLiveApi:{dataset:async()=>({dataset}),evaluations:async()=>({evaluations:[]}),evaluation:async()=>({evaluation}),...overrides},
    onMounted:f=>mounted=f,onBeforeUnmount:f=>unmounted=f,registerIdentityGuard:f=>{guard=f;return ()=>{}},
    setTimeout:f=>{timers.set(++nextTimer,f);return nextTimer},clearTimeout:id=>timers.delete(id),downloadJSON:(value,name)=>downloads.push({value,name}),
  }
  return {bindings,timers,downloads,mount:()=>mounted(),unmount:()=>unmounted(),guard:reason=>guard(reason)}
}
const component='components/TutorLiveEvaluation.vue'
const settle=async()=>{for(let i=0;i<6;i++)await nextTick()}

test('mount restores paid request and loads config, dataset and history using GET only',async()=>{
  let starts=0;const e=env({create:async()=>{starts++;return {evaluation}}})
  const body={requestId:'persisted-token',caseIds:['confusion'],repeats:1,maxCalls:4}
  localStorage.setItem('examhub:tutor:live-start:owner',JSON.stringify({body}))
  const vm=await script(component,e.bindings,names);e.mount();await settle()
  assert.equal(starts,0);assert.deepEqual(vm.pending.value.body,body)
  assert.equal(vm.config.value.model,'configured-model');assert.equal(vm.dataset.value.hash,'data-hash')
  assert.equal(vm.canStart.value,false)
  await vm.start(true);assert.equal(starts,1);assert.equal(vm.evaluation.value.id,'job-A')
})

test('new start requires loaded configuration, valid budget, available cases and explicit cost consent',async()=>{
  let starts=0
  const e=env({create:async body=>{starts++;assert.equal(JSON.parse(localStorage.getItem('examhub:tutor:live-start:owner')).body.requestId,body.requestId);return {evaluation}}})
  const vm=await script(component,e.bindings,names)
  vm.caseIds.value=['confusion'];vm.paidConfirmed.value=true
  await vm.start();assert.equal(starts,0)
  await vm.load();vm.paidConfirmed.value=false;await vm.start();assert.equal(starts,0)
  vm.paidConfirmed.value=true;vm.maxCalls.value=21;await vm.start();assert.equal(starts,0)
  vm.maxCalls.value=4;vm.caseIds.value=['not-in-dataset'];await vm.start();assert.equal(starts,0)
  vm.caseIds.value=['confusion'];await vm.start();assert.equal(starts,1)
  assert.equal(vm.paidConfirmed.value,false)
})

test('lost-response retry ignores edited form and an unresolved request blocks a second paid start',async()=>{
  const bodies=[],e=env({create:async body=>{bodies.push(structuredClone(body));if(bodies.length===1)throw new Error('lost');return {evaluation}}})
  const vm=await script(component,e.bindings,names);await vm.load()
  vm.caseIds.value=['confusion'];vm.repeats.value=2;vm.maxCalls.value=5;vm.paidConfirmed.value=true
  await vm.start();assert.equal(vm.pending.value.body.maxCalls,5)
  vm.caseIds.value=['reason'];vm.repeats.value=3;vm.maxCalls.value=20
  await vm.start();assert.equal(bodies.length,1)
  await vm.start(true);assert.equal(bodies.length,2);assert.deepEqual(bodies[0],bodies[1])
})

test('polling is read-only and late selected-job or lower-version responses cannot replace current progress',async()=>{
  const old=deferred(),newest=deferred();let count=0
  const running={...evaluation,status:'running',version:8}
  const e=env({evaluation:async id=>{count++;if(count===1)return old.promise;if(count===2)return {evaluation:{...running,id}};return newest.promise}})
  const vm=await script(component,e.bindings,names)
  const first=vm.selectEvaluation('job-A');await vm.selectEvaluation('job-B')
  assert.equal(vm.evaluation.value.id,'job-B');assert.equal(e.timers.size,1)
  old.resolve({evaluation});await first;assert.equal(vm.evaluation.value.id,'job-B')
  const read=vm.refresh();newest.resolve({evaluation:{...evaluation,id:'job-B',version:2}});await read
  assert.equal(vm.evaluation.value.version,8);assert.equal(vm.evaluation.value.status,'running')
})

test('freeze invalidates generations even if the same owner is later resumed, and unmount stops polling',async()=>{
  const wait=deferred(),resumed=deferred();let reads=0
  const e=env({evaluation:()=>++reads===1?wait.promise:resumed.promise})
  const vm=await script(component,e.bindings,names)
  const read=vm.selectEvaluation('job-A')
  e.bindings.sessionFrozen.value=true;e.guard('preserve');e.bindings.sessionFrozen.value=false
  wait.resolve({evaluation});await read;assert.equal(vm.evaluation.value,undefined)
  resumed.resolve({evaluation:{...evaluation,status:'running'}});await settle();assert.equal(e.timers.size,1)
  e.unmount();assert.equal(e.timers.size,0)
})

test('history and blind export ignore stale identity, and downloads contain only the server blind package',async()=>{
  const history=deferred(),blind=deferred(),e=env({evaluations:()=>history.promise,blind:()=>blind.promise})
  const vm=await script(component,e.bindings,names);vm.selectedId.value=evaluation.id;vm.evaluation.value=evaluation
  const listing=vm.loadHistory(),download=vm.downloadBlind()
  e.bindings.user.value={id:'different-owner'};await nextTick()
  history.resolve({evaluations:[evaluation]});blind.resolve({package:blindPackage});await Promise.all([listing,download])
  assert.equal(vm.history.value.length,0);assert.equal(e.downloads.length,0)
  vm.downloadReport();assert.equal(e.downloads.length,0)
  e.bindings.user.value={id:'owner'};await nextTick();await vm.downloadBlind()
  assert.equal(e.downloads.length,1);assert.deepEqual(e.downloads[0].value,blindPackage)
  assert.equal(e.downloads[0].name,'tutor-blind-review.json')
})

test('cancellation saves server outcome without restarting and ignores a late mutation after identity freeze',async()=>{
  const wait=deferred();let cancellations=0
  const e=env({cancel:()=>{cancellations++;return wait.promise}})
  const vm=await script(component,e.bindings,names);vm.selectedId.value=evaluation.id;vm.evaluation.value={...evaluation,status:'running'}
  const cancel=vm.cancel();assert.equal(e.guard('confirm'),false)
  e.bindings.sessionFrozen.value=true;e.guard('preserve')
  wait.resolve({evaluation:{...evaluation,version:5,status:'cancelled'}});await cancel
  assert.equal(cancellations,1);assert.equal(vm.evaluation.value.status,'running');assert.equal(e.timers.size,0)
})

test('manual review needs four actual scores and explanations, uses captured CAS and preserves draft on 409',async()=>{
  const reviews=[],notifications=[];let gets=0
  const e=env({blind:async()=>({package:blindPackage}),evaluation:async()=>{gets++;return {evaluation:{...evaluation,version:9}}},review:async(id,blindId,body)=>{reviews.push({id,blindId,body});if(reviews.length===1)throw Object.assign(new Error('version conflict'),{status:409});return {evaluation:{...evaluation,version:10}}}})
  e.bindings.notify=value=>notifications.push(value)
  const vm=await script(component,e.bindings,names);vm.selectedId.value=evaluation.id;vm.evaluation.value=evaluation
  await vm.loadBlind();vm.beginReview('blind-one')
  assert.deepEqual(vm.scores.value,{accuracy:null,grounding:null,diagnosis:null,actionability:null})
  vm.reviewer.value='  Reviewer  ';await vm.saveReview();assert.equal(reviews.length,0)
  vm.reviewerType.value='ai-assisted'
  vm.scores.value={accuracy:2,grounding:1,diagnosis:0,actionability:2}
  vm.notes.value={accuracy:'事实核验',grounding:'缺一处出处',diagnosis:'未指出混淆',actionability:'下一步清楚'}
  await vm.saveReview()
  assert.equal(reviews[0].body.version,3);assert.equal(reviews[0].body.reviewer,'Reviewer');assert.equal(reviews[0].body.reviewerType,'ai-assisted')
  assert.equal(reviews[0].blindId,'blind-one');assert.match(reviews[0].body.notes,/未指出混淆/)
  assert.equal(gets,1);assert.equal(vm.reviewConflict.value,true);assert.equal(vm.reviewVersion.value,3)
  assert.equal(vm.notes.value.diagnosis,'未指出混淆');assert.equal(vm.evaluation.value.version,9)
  await vm.saveReview();assert.equal(reviews.length,1)
  vm.rebaseReview();await vm.saveReview();assert.equal(reviews[1].body.version,9)
  assert.equal(vm.evaluation.value.version,10)
  assert.deepEqual(notifications,['复核结果已保存'])
})

test('report renders failure and unused denominator, nullable usage, repeated trials and pending human quality honestly',async()=>{
  const e=env()
  const html=await renderView(component,e.bindings,names,vm=>{vm.evaluation.value=evaluation;vm.selectedId.value=evaluation.id})
  assert.match(html,/固定学生/);assert.match(html,/不代表.*学习/)
  assert.match(html,/0 \/ 2/);assert.match(html,/预算耗尽/);assert.match(html,/供应商失败/)
  assert.match(html,/usage 未返回/);assert.match(html,/尚未人工复核/);assert.match(html,/第 1 次/)
  assert.doesNotMatch(html,/学习提升率|掌握率/)
})

test('cancelled job remains read-only while worker is busy and permits review only after busy clears',async()=>{
  let gets=0,blindReads=0
  const e=env({cancel:async()=>({evaluation:{...evaluation,status:'cancelled',busy:true,version:4}}),evaluation:async()=>{gets++;return {evaluation:{...evaluation,status:'cancelled',busy:false,version:5}}},blind:async()=>{blindReads++;return {package:blindPackage}}})
  const vm=await script(component,e.bindings,names);await vm.load()
  vm.selectedId.value=evaluation.id;vm.evaluation.value={...evaluation,status:'running'}
  vm.paidConfirmed.value=true
  await vm.cancel();assert.equal(vm.evaluation.value.status,'cancelled');assert.equal(vm.running.value,true)
  assert.equal(vm.canStart.value,false);assert.equal(e.timers.size,1)
  await vm.loadBlind();assert.equal(blindReads,0)
  await [...e.timers.values()][0]();await settle()
  assert.equal(gets,1);assert.equal(vm.running.value,false);assert.equal(e.timers.size,0)
  await vm.loadBlind();assert.equal(blindReads,1)
})

test('late paid start after freeze and resume preserves request for explicit retry instead of adopting its result',async()=>{
  const wait=deferred(),e=env({create:()=>wait.promise})
  const vm=await script(component,e.bindings,names);await vm.load();vm.paidConfirmed.value=true
  const start=vm.start();assert.equal(vm.busy.value,true)
  e.bindings.sessionFrozen.value=true;e.guard('preserve');e.bindings.sessionFrozen.value=false
  wait.resolve({evaluation});await start
  assert.equal(vm.evaluation.value,undefined);assert.ok(localStorage.getItem('examhub:tutor:live-start:owner'))
  assert.equal(vm.pending.value.body.maxCalls,10)
})

test('changing jobs during blind-package GET clears loading and discards the previous job package',async()=>{
  const wait=deferred(),e=env({blind:()=>wait.promise,evaluation:async id=>({evaluation:{...evaluation,id}})})
  const vm=await script(component,e.bindings,names);vm.selectedId.value=evaluation.id;vm.evaluation.value=evaluation
  const read=vm.loadBlind();assert.equal(vm.blindLoading.value,true)
  await vm.selectEvaluation('job-B');assert.equal(vm.blindLoading.value,false)
  wait.resolve({package:blindPackage});await read
  assert.equal(vm.blindPackage.value,undefined);assert.equal(vm.blindLoading.value,false)
})

test('same-owner reconciliation resumes only GETs after a frozen bootstrap without replaying pending start',async()=>{
  const wait=deferred();let datasets=0,creates=0
  const e=env({dataset:()=>++datasets===1?wait.promise:Promise.resolve({dataset}),create:async()=>{creates++;return {evaluation}}})
  localStorage.setItem('examhub:tutor:live-start:owner',JSON.stringify({body:{requestId:'stable',caseIds:['confusion'],repeats:1,maxCalls:4}}))
  const vm=await script(component,e.bindings,names);e.mount()
  e.bindings.sessionFrozen.value=true;e.guard('preserve');e.bindings.sessionFrozen.value=false
  await settle();assert.equal(datasets,2);assert.equal(vm.loading.value,false);assert.equal(creates,0)
  wait.resolve({dataset:{...dataset,hash:'stale-hash'}});await settle()
  assert.equal(vm.dataset.value.hash,'data-hash');assert.equal(vm.pending.value.body.requestId,'stable')
})

test('completed job can have zero completed agent trials and saved AI-assisted reviews remain explicitly labelled',async()=>{
  const e=env(),review={reviewer:'Reviewer',reviewerType:'ai-assisted',scores:{accuracy:1,grounding:0,diagnosis:1,actionability:0},notes:'根据实际固定回答与反馈复核',updatedAt:'2026-10-20'}
  const value={...evaluation,status:'completed',modelCalls:20,maxCalls:20,report:{...evaluation.report,trials:evaluation.report.trials.map(t=>({...t,status:'budget',review})),summary:{...evaluation.report.summary,agent:{trials:2,completed:0,passed:0,checks:2,passedChecks:0,modelCalls:20}}}}
  const html=await renderView(component,e.bindings,names,vm=>{vm.evaluation.value=value;vm.selectedId.value=value.id;vm.blindPackage.value=blindPackage;vm.beginReview('blind-one')})
  assert.match(html,/已完成/);assert.match(html,/完成 0 \/ 2/);assert.match(html,/行为通过 0 \/ 2/)
  assert.match(html,/预算耗尽/);assert.match(html,/AI 辅助复核 · 非独立人工评分/);assert.match(html,/已计入调用预算 20 \/ 20/)
  assert.match(html,/计数包含请求发送前预留；中断时不等于供应商计费次数，usage 为实际返回/)
  assert.doesNotMatch(html,/AI 辅助人工|已保存的人工复核/)
  assert.match(html,/作业完成表示执行已结束/)
})

test('reproducibility metadata displays grader version or unknown and preserves historical check counts',async()=>{
  for(const graderVersion of ['v1','v2','live-behavior-v1','live-behavior-v2',undefined]){
    const e=env(),value={...evaluation,report:{...evaluation.report,graderVersion,summary:{...evaluation.report.summary,agent:{...evaluation.report.summary.agent,passedChecks:3,checks:13}}}}
    const html=await renderView(component,e.bindings,names,vm=>{vm.evaluation.value=value;vm.selectedId.value=value.id})
    assert.ok(html.includes(`行为判据 ${graderVersion||'未记录'}`))
    assert.match(html,/相同行为判据版本/)
    assert.match(html,/检查通过 3 \/ 13/)
    const historicalNote='历史判据 v1 的动作检查还要求正常结束，预算耗尽也记为未通过；原始结果保留，与新版分数不能直接比较'
    assert.equal(html.includes(historicalNote),graderVersion==='live-behavior-v1')
    if(graderVersion==='live-behavior-v1')assert.ok(html.indexOf(historicalNote)<html.indexOf('<details>'))
  }
})
