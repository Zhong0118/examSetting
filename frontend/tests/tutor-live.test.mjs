import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { script, storage, deferred } from './harness.mjs'

const originalFetch=globalThis.fetch
afterEach(()=>{globalThis.fetch=originalFetch})
const load=bindings=>script('lib/tutorLive.ts',bindings,['tutorLiveApi','createLiveStartRequest','liveStartValid'])

test('lost start response retains persisted immutable payload and explicit retry uses the same requestId',async()=>{
  const {createLiveStartRequest}=await load({request:()=>{}})
  const store=storage(),bodies=[];let state,received
  const flow=createLiveStartRequest(store,'owner:pending',async body=>{
    assert.deepEqual(JSON.parse(store.getItem('owner:pending')).body,body)
    bodies.push(structuredClone(body))
    if(bodies.length===1)throw new Error('response lost')
    return {id:'job',version:1}
  },value=>state=value,value=>received=value)
  const input={caseIds:['confusion'],repeats:2,maxCalls:8}
  await assert.rejects(flow.submit(input),/response lost/)
  input.caseIds.push('other');input.maxCalls=20
  assert.equal(state.body.caseIds.length,1);assert.equal(state.body.maxCalls,8)
  assert.equal(received,undefined)
  await flow.retry()
  assert.deepEqual(bodies[1],bodies[0]);assert.ok(bodies[0].requestId)
  assert.equal(received.id,'job');assert.equal(store.getItem('owner:pending'),null)
})

test('restoration never sends and cannot replace an unknown paid request with a new payload',async()=>{
  const {createLiveStartRequest}=await load({request:()=>{}})
  const store=storage();let calls=0
  const body={requestId:'existing-request',caseIds:['a'],repeats:1,maxCalls:4}
  store.setItem('pending',JSON.stringify({body}))
  const flow=createLiveStartRequest(store,'pending',async()=>{calls++},()=>{},()=>{})
  assert.deepEqual(flow.restore().body,body);assert.equal(calls,0)
  await assert.rejects(flow.submit({caseIds:['b'],repeats:3,maxCalls:20}),/待确认/)
  assert.throws(()=>flow.discard(),/原请求/);assert.equal(calls,0)
})

test('failed persistence prevents POST and definitive rejection is archived before a new start',async()=>{
  const {createLiveStartRequest}=await load({request:()=>{}})
  let calls=0
  const broken={getItem:()=>null,setItem:()=>{throw new Error('quota exceeded')},removeItem:()=>{}}
  const flow=createLiveStartRequest(broken,'pending',async()=>{calls++},()=>{},()=>{})
  await assert.rejects(flow.submit({caseIds:['a'],repeats:1,maxCalls:2}),/quota exceeded/)
  assert.equal(calls,0)
  const store=storage()
  const rejected=createLiveStartRequest(store,'pending',async()=>{calls++;throw Object.assign(new Error('invalid'),{status:422})},()=>{},()=>{})
  await assert.rejects(rejected.submit({caseIds:['a'],repeats:1,maxCalls:2}),/invalid/)
  const pending=JSON.parse(store.getItem('pending'));assert.equal(pending.blocked,true)
  await assert.rejects(rejected.retry());assert.equal(calls,1)
  rejected.discard();assert.equal(store.getItem('pending'),null)
  assert.deepEqual(JSON.parse(store.getItem(`pending:archive:${pending.body.requestId}`)),pending)
})

test('stale identity, replaced envelope and disposal cannot consume or display a late start result',async()=>{
  const {createLiveStartRequest}=await load({request:()=>{}})
  for(const change of ['identity','replacement','dispose']){
    const store=storage(),wait=deferred();let active=true,received=0
    const flow=createLiveStartRequest(store,'pending',()=>wait.promise,()=>{},()=>received++,()=>active)
    const pending=flow.submit({caseIds:['a'],repeats:1,maxCalls:2})
    if(change==='identity')active=false
    if(change==='replacement')store.setItem('pending',JSON.stringify({body:{requestId:'newer'}}))
    if(change==='dispose')flow.dispose()
    wait.resolve({id:'old',version:1});await pending
    assert.equal(received,0);assert.ok(store.getItem('pending'))
  }
})

test('start validation enforces unique nonempty cases, integral repeats and a 20-call ceiling',async()=>{
  const {liveStartValid}=await load({request:()=>{}})
  assert.equal(liveStartValid({caseIds:['a','b'],repeats:3,maxCalls:20}),true)
  for(const input of [
    {caseIds:[],repeats:1,maxCalls:2},{caseIds:['a','a'],repeats:1,maxCalls:2},
    {caseIds:[''],repeats:1,maxCalls:2},{caseIds:['a','b','c','d','e'],repeats:1,maxCalls:2},
    {caseIds:['a'],repeats:0,maxCalls:2},{caseIds:['a'],repeats:1.5,maxCalls:2},
    {caseIds:['a'],repeats:4,maxCalls:2},{caseIds:['a'],repeats:1,maxCalls:21},
    {caseIds:['a'],repeats:1,maxCalls:0},{caseIds:['a'],repeats:1,maxCalls:1.5},
  ])assert.equal(liveStartValid(input),false,JSON.stringify(input))
})

test('live API keeps exact spec bodies, encoded owner-scoped paths and expected-user protection',async()=>{
  const client=await script('lib/api.ts',{},['request','setExpectedUser'])
  client.setExpectedUser('owner')
  const {tutorLiveApi}=await load({request:client.request}),calls=[]
  globalThis.fetch=async(url,options)=>{calls.push({url,...options});return Response.json({evaluation:{id:'job'}})}
  await tutorLiveApi.dataset();await tutorLiveApi.evaluations()
  const body={requestId:'persisted-token',caseIds:['a'],repeats:2,maxCalls:20}
  await tutorLiveApi.create(body);await tutorLiveApi.evaluation('job/1');await tutorLiveApi.cancel('job/1');await tutorLiveApi.blind('job/1')
  const review={version:4,reviewer:'R',reviewerType:'ai-assisted',scores:{accuracy:2,grounding:1,diagnosis:0,actionability:2},notes:'逐项说明'}
  await tutorLiveApi.review('job/1','blind/1',review)
  assert.deepEqual(calls.map(c=>[c.url,c.method]),[
    ['/api/tutor/live-evaluations/dataset','GET'],['/api/tutor/live-evaluations','GET'],
    ['/api/tutor/live-evaluations','POST'],['/api/tutor/live-evaluations/job%2F1','GET'],
    ['/api/tutor/live-evaluations/job%2F1/cancel','POST'],['/api/tutor/live-evaluations/job%2F1/blind','GET'],
    ['/api/tutor/live-evaluations/job%2F1/reviews/blind%2F1','PUT'],
  ])
  assert.deepEqual(JSON.parse(calls[2].body),body);assert.deepEqual(JSON.parse(calls[6].body),review)
  assert.equal(calls[2].headers['X-Expected-User'],'owner');assert.equal(calls[6].headers['X-Expected-User'],'owner')
})
