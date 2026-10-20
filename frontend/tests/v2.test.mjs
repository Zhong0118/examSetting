import {test,afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {script} from './harness.mjs'
const fetchBefore=globalThis.fetch
afterEach(()=>{globalThis.fetch=fetchBefore})
test('V2 multipart upload preserves identity protection and lets browser set boundary',async()=>{
  const a=await script('lib/api.ts',{},['api','setExpectedUser']);a.setExpectedUser('user-a')
  let request
  globalThis.fetch=async(url,init)=>{request={url,...init};return Response.json({document:{id:'doc'},duplicate:false},{status:201})}
  assert.equal(typeof a.api.uploadDocument,'function')
  await a.api.uploadDocument(new File(['%PDF-test'],'text.pdf',{type:'application/pdf'}))
  assert.equal(request.headers['X-Expected-User'],'user-a');assert.equal(request.headers['X-Requested-With'],'ExamHub')
  assert.equal(request.headers['Content-Type'],undefined);assert.ok(request.body instanceof FormData);assert.equal(request.body.get('file').name,'text.pdf')
})
