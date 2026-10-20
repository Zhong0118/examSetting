import {test} from 'node:test'
import assert from 'node:assert/strict'
import {script,storage,deferred} from './harness.mjs'
const {createComparison}=await script('lib/comparison.ts',{},['createComparison'])
const input={documentId:'D',startPage:1,endPage:1,count:1,title:'T',topic:''}
const job=(id,status='completed')=>({id,status,metadata:{metricsFinalized:true}})
test('late disposed GET cannot overwrite completed state from a newer instance',async()=>{
 const local=storage(),late=deferred(),old=createComparison({startJob:async()=>({job:job('B','running')}),job:()=>late.promise},local,'k',()=>{})
 await old.start(input);const waiting=old.tick();old.dispose()
 const fresh=createComparison({job:async()=>({job:job('B')}),startJob:async()=>({job:job('G')}),createEvaluation:async()=>({evaluation:{id:'E'}})},local,'k',()=>{})
 fresh.restore();await fresh.resume();late.resolve({job:job('B','running')});await waiting
 assert.equal(JSON.parse(local.getItem('k')).phase,'done');assert.equal(JSON.parse(local.getItem('k')).evaluation.id,'E')
})
test('permanent report error can be ended with archived evidence and allows another comparison',async()=>{
 const local=storage();local.setItem('k',JSON.stringify({input,phase:'report',paused:true,baseline:job('B'),grounded:job('G')}))
 const flow=createComparison({createEvaluation:async()=>{throw Object.assign(new Error('模型不同'),{status:400})},startJob:async()=>({job:job('new','running')})},local,'k',()=>{})
 flow.restore();await assert.rejects(flow.resume());flow.end()
 const archives=[...local.map.entries()].filter(([k])=>k.startsWith('k:archive:'));assert.equal(archives.length,1);assert.equal(JSON.parse(archives[0][1]).grounded.id,'G')
 await flow.start(input);assert.equal(JSON.parse(local.getItem('k')).baseline.id,'new')
})
test('report recovery needs no key while creating next model task uses explicit guard',async()=>{
 const local=storage();local.setItem('k',JSON.stringify({input,phase:'report',paused:true,baseline:job('B'),grounded:job('G')}));let guards=0
 const flow=createComparison({createEvaluation:async()=>({evaluation:{id:'E'}})},local,'k',()=>{},async()=>{guards++;throw new Error('请配置密钥')})
 flow.restore();await flow.resume();assert.equal(guards,0)
 await assert.rejects(flow.start(input),/密钥/);assert.equal(guards,1)
})
test('lost accepted job response reuses persisted token after reload with no second model call',async()=>{
 const local=storage(),accepted=new Map(),tokens=[];let lose=true,guards=0
 const service={startJob:async data=>{
  assert.equal(JSON.parse(local.getItem('k')).requestIds[data.strategy],data.requestId)
  assert.match(data.requestId,/^[A-Za-z0-9_-]{16,100}$/);tokens.push(data.requestId)
  if(!accepted.has(data.requestId))accepted.set(data.requestId,job('B','running'))
  if(lose){lose=false;throw new Error('lost response after commit')}
  return {job:accepted.get(data.requestId)}
 }}
 const first=createComparison(service,local,'k',()=>{},async()=>{guards++})
 await assert.rejects(first.start(input));first.dispose()
 const next=createComparison(service,local,'k',()=>{},async()=>{throw new Error('key was lost on restart')})
 next.restore();await next.resume();assert.equal(accepted.size,1);assert.equal(tokens[0],tokens[1]);assert.equal(guards,1)
})
test('lost report response retries same pair and creates only one idempotent snapshot',async()=>{
 const local=storage(),snapshots=new Map();let lose=true,starts=0
 const service={startJob:async data=>{starts++;return {job:job(data.strategy)}},createEvaluation:async ids=>{
  const key=[...ids].sort().join(',');if(!snapshots.has(key))snapshots.set(key,{id:'E'})
  if(lose){lose=false;throw new Error('lost response after report commit')}
  return {evaluation:snapshots.get(key)}
 }}
 const first=createComparison(service,local,'k',()=>{});await assert.rejects(first.start(input));first.dispose()
 const next=createComparison(service,local,'k',()=>{});next.restore();await next.resume()
 assert.equal(starts,2);assert.equal(snapshots.size,1);assert.equal(JSON.parse(local.getItem('k')).evaluation.id,'E')
})
test('late POST from superseded same-account instance cannot overwrite newer revision',async()=>{
 const local=storage(),late=deferred();let first=true;const tokens=[]
 const service={startJob:async data=>{tokens.push(data.requestId);if(first){first=false;return late.promise}return {job:job(data.strategy)}},createEvaluation:async()=>({evaluation:{id:'E'}})}
 const old=createComparison(service,local,'k',()=>{});const pending=old.start(input);await Promise.resolve()
 const fresh=createComparison(service,local,'k',()=>{});fresh.restore();await fresh.resume()
 late.resolve({job:job('baseline','running')});await pending
 assert.equal(JSON.parse(local.getItem('k')).phase,'done');assert.equal(tokens[0],tokens[1]);assert.notEqual(tokens[1],tokens[2])
})
test('polling without key stops before new strategy creation while retaining first job',async()=>{
 const local=storage();local.setItem('k',JSON.stringify({input,phase:'baseline',paused:true,baseline:job('B','running')}));let posts=0
 const flow=createComparison({job:async()=>({job:job('B')}),startJob:async()=>{posts++;return {job:job('G')}}},local,'k',()=>{},async()=>{throw new Error('请配置密钥')})
 flow.restore();await assert.rejects(flow.resume(),/密钥/);assert.equal(posts,0)
 const saved=JSON.parse(local.getItem('k'));assert.equal(saved.phase,'grounded');assert.equal(saved.baseline.id,'B');assert.equal(saved.requestIds.grounded,undefined)
})
test('request token derives from persisted operation for each strategy',async()=>{
 const local=storage(),ids=[]
 const flow=createComparison({startJob:async data=>{const saved=JSON.parse(local.getItem('k'));assert.equal(data.requestId,`${saved.operationId}-${data.strategy}`);ids.push(data.requestId);return {job:job(data.strategy)}},createEvaluation:async()=>({evaluation:{id:'E'}})},local,'k',()=>{})
 await flow.start(input);assert.notEqual(ids[0],ids[1])
})
test('resume button permits saved report recovery without configured key',async()=>{
 const {readFile}=await import('node:fs/promises');const view=await readFile(new URL('../src/views/EvaluationsView.vue',import.meta.url),'utf8')
 const button=view.match(/<button v-if="state\?\.paused"[^>]+>/)[0]
 const disabled=button.match(/:disabled="([^"]+)"/)[1]
 assert.equal(new Function('busy','config',`return (${disabled})`)(false,{configured:false}),false)
})
test('evaluation status distinguishes unacknowledged job and suppresses duplicate error',async()=>{
 const {readFile}=await import('node:fs/promises'),{renderView}=await import('./harness.mjs'),{ref}=await import('vue')
 const docs=await script('lib/documents.ts',{},['percent','qualityLabel'])
 globalThis.localStorage=storage()
 const html=await renderView('views/EvaluationsView.vue',{useRoute:()=>({query:{}}),user:ref({id:'U'}),api:{},createComparison:()=>({}),registerIdentityGuard:()=>()=>{},...docs},['benchmark','benchmarkBusy','benchmarkError','selection','unfinished','busy','config','state','error','selected','history','labels','count','archives'],vm=>{vm.state.value={input,phase:'baseline',paused:true,requestIds:{baseline:'pending-token'},error:'连接中断待恢复'};vm.error.value='连接中断待恢复'})
 assert.match(html,/等待恢复任务状态/);assert.equal(html.split('连接中断待恢复').length,2)
})
