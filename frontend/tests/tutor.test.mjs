import {test} from 'node:test'
import assert from 'node:assert/strict'
import {script,storage,deferred} from './harness.mjs'
const operation={kind:'command',sessionId:'S',body:{type:'answer',version:4,turnId:2,answer:'A'}}
test('tutor accepted POST response loss retries exact persisted token and payload after remount',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest'])
 const local=storage(),sent=[];let first=true
 const send=async op=>{assert.deepEqual(JSON.parse(local.getItem('k')).operation,op);sent.push(op);if(first){first=false;throw new Error('network lost')}return {id:'S',version:5}}
 const old=createTutorRequest(local,'k',send,()=>{},()=>{});await assert.rejects(old.submit(operation));old.dispose()
 let session;const next=createTutorRequest(local,'k',send,()=>{},s=>session=s);next.restore();assert.equal(sent.length,1)
 await next.retry();assert.deepEqual(sent[0],sent[1]);assert.match(sent[0].body.requestId,/^[a-zA-Z0-9_-]{16,100}$/);assert.equal(session.version,5);assert.equal(local.getItem('k'),null)
})
test('tutor conflict blocks automatic replay and archives old answer before explicit fresh command',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest']);const local=storage();let sent=0
 const flow=createTutorRequest(local,'k',async()=>{sent++;throw Object.assign(new Error('version conflict'),{status:409})},()=>{},()=>{})
 await assert.rejects(flow.submit(operation));await assert.rejects(flow.retry());assert.equal(sent,1);flow.discard()
 const archive=[...local.map.entries()].find(([k])=>k.startsWith('k:archive:'));assert.equal(JSON.parse(archive[1]).operation.body.answer,'A');assert.equal(local.getItem('k'),null)
})
test('tutor unmount or identity freeze cannot consume pending request or publish stale session',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest'])
 for(const dispose of [true,false]){const local=storage(),wait=deferred();let active=true,updates=0;const flow=createTutorRequest(local,'k',()=>wait.promise,()=>{},()=>updates++,()=>active)
 const pending=flow.submit(operation);if(dispose)flow.dispose();else active=false;wait.resolve({id:'S',version:5});await pending
 assert.equal(updates,0);assert.ok(local.getItem('k'))}
})
test('tutor reader discards out-of-order and disposed reads',async()=>{
 const {createTutorReader}=await script('lib/tutorRequests.ts',{},['createTutorReader']);const a=deferred(),b=deferred(),applied=[];let reads=0
 const flow=createTutorReader(()=>++reads===1?a.promise:b.promise,s=>applied.push(s.version))
 const one=flow.read(),two=flow.read();b.resolve({id:'S',version:3});await two;a.resolve({id:'S',version:2});await one;assert.deepEqual(applied,[3])
 flow.dispose();await flow.read();assert.equal(reads,2)
})
test('tutor reads are read-only and restoring an outstanding create never auto-POSTs',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest']);const local=storage();let calls=0
 local.setItem('k',JSON.stringify({operation:{kind:'create',body:{requestId:'existing-token-12345',setId:'s',goal:'goal',mode:'rule',maxQuestions:1}}}))
 const flow=createTutorRequest(local,'k',async()=>{calls++;return {id:'S',version:1}},()=>{},()=>{})
 flow.restore();assert.equal(calls,0);await flow.retry();assert.equal(calls,1)
})
test('tutor old response does not remove a newer cross-tab pending operation',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest']);const local=storage(),pending=deferred();let applied=0
 const flow=createTutorRequest(local,'k',()=>pending.promise,()=>{},()=>applied++)
 const send=flow.submit(operation);local.setItem('k',JSON.stringify({operation:{...operation,body:{...operation.body,requestId:'newer-token-12345'}}}))
 pending.resolve({id:'S',version:5});await send;assert.equal(applied,0);assert.match(local.getItem('k'),/newer-token-12345/)
})
test('tutor identity session_changed is never converted into a version-conflict discard',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest']);const local=storage()
 const flow=createTutorRequest(local,'k',async()=>{throw Object.assign(new Error('identity changed'),{status:409,code:'session_changed'})},()=>{},()=>{})
 await assert.rejects(flow.submit(operation));assert.equal(JSON.parse(local.getItem('k')).blocked,undefined)
 assert.throws(()=>flow.discard(),/尚不确定/)
})
test('tutor refusing storage persistence never sends a write',async()=>{
 const {createTutorRequest}=await script('lib/tutorRequests.ts',{},['createTutorRequest']);let sends=0
 const flow=createTutorRequest({getItem:()=>null,setItem:()=>{throw new Error('quota exceeded')}},'k',async()=>{sends++;return {}},()=>{},()=>{})
 await assert.rejects(flow.submit(operation),/quota/);assert.equal(sends,0)
})
