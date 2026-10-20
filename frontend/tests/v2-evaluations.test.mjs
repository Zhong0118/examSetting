import {test} from 'node:test'
import assert from 'node:assert/strict'
import {script,storage,deferred,renderView} from './harness.mjs'
const {createComparison}=await script('lib/comparison.ts',{},['createComparison'])
const docs=await script('lib/documents.ts',{},['selectionError','percent','qualityLabel'])
const input={documentId:'D',startPage:1,endPage:2,count:2,title:'T'}
const job=(id,status='completed',final=true)=>({id,status,metadata:{metricsFinalized:final}})
test('comparison waits for cancelled worker finalization, then includes failure in sequential snapshot',async()=>{
 const calls=[],local=storage();let current;let final=false
 const service={startJob:async i=>{calls.push(i.strategy);return {job:job(i.strategy,i.strategy==='baseline'?'cancelled':'failed',i.strategy!=='baseline')}},job:async id=>{calls.push(`read:${id}`);return {job:job(id,'cancelled',final)}},createEvaluation:async ids=>{calls.push(ids);return {evaluation:{id:'E'}}}}
 const flow=createComparison(service,local,'key',s=>current=s)
 await flow.start(input);assert.deepEqual(calls,['baseline']);assert.equal(current.phase,'baseline')
 await flow.tick();assert.deepEqual(calls,['baseline','read:baseline'])
 final=true;await flow.tick();assert.deepEqual(calls,['baseline','read:baseline','read:baseline','grounded',['baseline','grounded']]);assert.equal(current.phase,'done')
 assert.equal(JSON.parse(local.getItem('key')).evaluation.id,'E')
})
test('restore is passive, resume polls saved job and never creates duplicate baseline',async()=>{
 const local=storage(),calls=[];local.setItem('key',JSON.stringify({input,phase:'baseline',paused:false,baseline:job('existing','running',false)}))
 const flow=createComparison({job:async id=>{calls.push(id);return {job:job(id)}},startJob:async i=>{calls.push(i.strategy);return {job:job('new')}},createEvaluation:async ids=>{calls.push(ids);return {evaluation:{id:'E'}}}},local,'key',()=>{})
 assert.equal(flow.restore().paused,true);await flow.tick();assert.deepEqual(calls,[])
 await flow.resume();assert.deepEqual(calls,['existing','grounded',['existing','new']])
})
test('dispose during accepted POST preserves job pointer without next strategy',async()=>{
 const pending=deferred(),local=storage(),calls=[]
 const flow=createComparison({startJob:async i=>{calls.push(i.strategy);return pending.promise}},local,'key',()=>{})
 const running=flow.start(input);await Promise.resolve();flow.dispose();pending.resolve({job:job('accepted')});await running
 assert.deepEqual(calls,['baseline']);assert.equal(JSON.parse(local.getItem('key')).baseline.id,'accepted')
})
test('immediately completed jobs create both sequentially and report once',async()=>{
 const calls=[];const flow=createComparison({startJob:async i=>{calls.push(i.strategy);return {job:job(i.strategy)}},createEvaluation:async()=>{calls.push('report');return {evaluation:{id:'E'}}}},storage(),'key',()=>{})
 await flow.start(input);await flow.tick();assert.deepEqual(calls,['baseline','grounded','report'])
})
test('PDF text selection matches server double newline boundary exactly',()=>{
 const pages=[{page:1,text:'a'.repeat(14999)},{page:2,text:'b'.repeat(14999)}]
 assert.equal(docs.selectionError(pages,1,2),'');pages[1].text+='b';assert.match(docs.selectionError(pages,1,2),/30000/)
 assert.match(docs.selectionError(pages,0,2),/有效/)
})
test('quality rendering uses question ordinals and Chinese labels, without duplicate disclaimer',async()=>{
 const report={ruleVersion:'v2',total:2,passed:0,items:[{questionId:'uuid-a',checks:[{code:'duplicate',status:'fail',message:'与 uuid-b 重复'}]},{questionId:'uuid-b',checks:[]}],duplicatePairs:[{left:'uuid-a',right:'uuid-b',similarity:1}],limits:['规则通过不等于事实正确']}
 const html=await renderView('components/QualityPanel.vue',{defineProps:()=>({report}),report,stale:false,...docs},['ordinal','checkMessage'])
 assert.match(html,/第 1 题 与 第 2 题/);assert.match(html,/题目重复/);assert.doesNotMatch(html,/uuid-a|uuid-b|duplicate/);assert.equal(html.split('规则通过不等于').length,2)
})
test('comparison snapshot displays interrupted timing as unknown and includes failed run',async()=>{
 const evaluation={id:'E',documentTitle:'教材',pages:[1],runs:[{jobId:'J',strategy:'baseline',status:'failed',elapsedMs:null,modelCalls:1,questionCount:0}],limitations:[]}
 const html=await renderView('components/ComparisonReport.vue',{defineProps:()=>({evaluation}),evaluation,date:()=>'',...docs},['labels','statuses'])
 assert.match(html,/耗时未知（计时中断）/);assert.match(html,/0 \/ 1/);assert.doesNotMatch(html,/0.00 秒/)
})
test('benchmark template explains labels and expands actual sample and expected defect',async()=>{
 const {ref}=await import('vue');globalThis.localStorage=storage()
 const html=await renderView('views/EvaluationsView.vue',{useRoute:()=>({query:{}}),user:ref({id:'U'}),api:{},createComparison:()=>({pause(){},dispose(){}}),registerIdentityGuard:()=>()=>{},...docs},['benchmark','benchmarkBusy','benchmarkError','selection','unfinished','busy','config','state','error','selected','history','labels','count','archives'],vm=>{vm.benchmark.value={datasetId:'test',datasetHash:'hash',sampleCount:1,ruleVersion:'v2',limitations:[],strategies:[{name:'grounded-v2',samples:[{id:'sample-id',label:true,predicted:false,description:'预期缺陷：缺少解析',questions:[{prompt:'实际测试题干',options:['甲','乙'],answer:'甲'}],issues:['explanation']}]}]}})
 assert.match(html,/标注有缺陷/);assert.match(html,/未检出/);assert.match(html,/实际测试题干/);assert.match(html,/预期缺陷：缺少解析/);assert.match(html,/答案解析/);assert.doesNotMatch(html,/标注 true|检出 false/)
})
test('restoring completed comparison keeps it completed without paused indication or network calls',async()=>{
 const local=storage();local.setItem('key',JSON.stringify({input,phase:'done',paused:false,evaluation:{id:'E'}}))
 const flow=createComparison({},local,'key',()=>{});const restored=flow.restore()
 assert.equal(restored.paused,false);assert.equal(restored.evaluation.id,'E');await flow.tick()
})
