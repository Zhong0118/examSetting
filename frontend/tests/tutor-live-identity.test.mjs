import test from 'node:test'
import assert from 'node:assert/strict'
import {script,storage} from './harness.mjs'

test('guest live evaluation retry token migrates unchanged and account copy wins',async()=>{
  globalThis.localStorage=storage()
  const {migrateGuestDrafts}=await script('lib/drafts.ts',{},['migrateGuestDrafts'])
  const key=id=>`examhub:tutor:live-start:${id}`
  const pending=JSON.stringify({body:{requestId:'immutable-paid-retry',caseIds:['tcp-misconception'],repeats:1,maxCalls:10}})
  localStorage.setItem(key('G'),pending)
  migrateGuestDrafts({id:'G',email:null},{id:'U',email:'u@example.test'})
  assert.equal(localStorage.getItem(key('U')),pending)
  assert.equal(localStorage.getItem(key('G')),pending)
  localStorage.setItem(key('U'),'account-request')
  assert.equal(migrateGuestDrafts({id:'G',email:null},{id:'U',email:'u@example.test'}),1)
  assert.equal(localStorage.getItem(key('U')),'account-request')
  migrateGuestDrafts({id:'U',email:'u@example.test'},{id:'V',email:'v@example.test'})
  assert.equal(localStorage.getItem(key('V')),null)
})
