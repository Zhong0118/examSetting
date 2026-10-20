import {test, afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {ref} from 'vue'
import {script,deferred,storage} from './harness.mjs'
const oldStorage=globalThis.localStorage,oldWindow=globalThis.window,oldFetch=globalThis.fetch
const no=()=>{}
afterEach(()=>{globalThis.localStorage=oldStorage;globalThis.window=oldWindow;globalThis.fetch=oldFetch})
const question={id:'q',type:'single',prompt:'Question',options:['A','B'],answer:'A',explanation:'',source:'',topic:''}
async function editor(api, extra={}){
  globalThis.window={confirm:()=>true,addEventListener:no,removeEventListener:no};globalThis.localStorage=storage()
  const pushes=[]
  const instance=await script('views/EditorView.vue',{useRoute:()=>({params:{id:'set'},path:'/sets/set/edit'}),useRouter:()=>({push:async p=>pushes.push(p)}),api,ApiError:Error,notify:no,message:e=>e.message,user:ref({id:'u'}),registerIdentityGuard:()=>no,...extra},['form','canEdit','save','dirty','load','reload','busy'])
  instance.canEdit.value=true;instance.form.value={title:'before',description:'',topic:'',visibility:'private',version:1,questions:[structuredClone(question)]}
  return {...instance,pushes}
}
test('review 3: edit while save is pending stays dirty and does not navigate',async()=>{
  const pending=deferred();const e=await editor({save:()=>pending.promise});const saving=e.save();e.form.value.title='changed during save'
  pending.resolve({set:{id:'set',version:2}});await saving
  assert.equal(e.dirty.value,true);assert.deepEqual(e.pushes,[]);assert.equal(e.form.value.version,2)
})
test('review 6: cancelled old poll cannot overwrite newly started AI job',async()=>{
  globalThis.localStorage=storage();const pending=deferred();const dispose=[]
  const a=await script('components/AIGenerator.vue',{defineProps:()=>({title:'T',topic:'T'}),defineEmits:()=>no,api:{job:()=>pending.promise,cancelJob:async()=>({job:{id:'old',status:'cancelled'}}),startJob:async()=>({job:{id:'new',status:'running'}})},message:e=>e.message,user:ref({id:'u'}),onBeforeUnmount:f=>dispose.push(f)},['job','source','poll','cancel','start'])
  a.job.value={id:'old',status:'running'};a.source.value='a'.repeat(30)
  try{const poll=a.poll();await a.cancel();await a.start();pending.resolve({job:{id:'old',status:'running'}});await poll;assert.equal(a.job.value.id,'new')}finally{dispose.forEach(f=>f())}
})
test('review 2: rejected dirty guard prevents auth request and identity assignment',async()=>{
  const calls=[];const current=ref({id:'guest',email:null})
  const a=await script('components/AuthDialog.vue',{useRouter:()=>({push:async()=>{}}),api:{auth:async()=>{calls.push('request');return {user:{id:'account'}}}},authOpen:ref(true),user:current,notify:no,message:e=>e.message,changeIdentity:async()=>false},['submit'])
  await a.submit();assert.deepEqual(calls,[]);assert.equal(current.value.id,'guest')
})
test('review 1: API exposes expected-identity setter and sends identity on auth writes',async()=>{
  const a=await script('lib/api.ts',{},['api','setExpectedUser']);assert.equal(typeof a.setExpectedUser,'function')
  a.setExpectedUser('old-guest');let headers
  globalThis.fetch=async(_,init)=>{headers=init.headers;return Response.json({user:{id:'new-account'}})}
  await a.api.auth('login',{email:'a@example.test',password:'password'});assert.equal(headers['X-Expected-User'],'old-guest')
})

async function state(api,extra={}){
  const identities=[],blocks=[]
  return {...await script('lib/state.ts',{api,setExpectedUser:id=>identities.push(id),setSessionBlocked:flag=>blocks.push(flag),onSessionChanged:no,migrateGuestDrafts:()=>0,setTimeout:()=>0,clearTimeout:no,...extra},['user','initSession','changeIdentity','freezeSession','sessionFrozen','identityChanging','registerIdentityGuard','reconcileSession','checkSession','handleSessionSignal']),identities,blocks}
}
test('review 1: every write, including login and logout, carries the old expected identity',async()=>{
  const a=await script('lib/api.ts',{},['api','setExpectedUser']);a.setExpectedUser('old')
  const headers=[];globalThis.fetch=async(_,init)=>{headers.push(init.headers);return Response.json({})}
  await Promise.all([a.api.save({}),a.api.save({},'s'),a.api.delete('s'),a.api.bookmark('s'),a.api.fork('s'),a.api.submit('s',1,{}),a.api.saveConfig({}),a.api.startJob({}),a.api.cancelJob('j'),a.api.auth('login',{}),a.api.auth('register',{}),a.api.logout()])
  assert.equal(headers.length,12);assert.ok(headers.every(h=>h['X-Expected-User']==='old'))
})
test('review 1: session_changed freezes client, blocks further reads/writes, allows reconciliation',async()=>{
  let changed=0,calls=0
  const a=await script('lib/api.ts',{},['api','setExpectedUser','onSessionChanged']);a.setExpectedUser('old');a.onSessionChanged(()=>changed++)
  globalThis.fetch=async()=>{calls++;return Response.json({error:'Changed',code:'session_changed'},{status:409})}
  await assert.rejects(a.api.submit('s',1,{}),e=>e.code==='session_changed'&&e.status===409);assert.equal(changed,1)
  await assert.rejects(a.api.startJob({}),e=>e.code==='session_changed');await assert.rejects(a.api.job('j'),e=>e.code==='session_changed');assert.equal(calls,1)
  globalThis.fetch=async()=>Response.json({user:{id:'new'}})
  assert.equal((await a.api.session()).user.id,'new')
})
test('review 1: a successful but stale in-flight response cannot be consumed after freezing',async()=>{
  const pending=deferred(),a=await script('lib/api.ts',{},['api','setExpectedUser','setSessionBlocked'])
  a.setExpectedUser('old');globalThis.fetch=()=>pending.promise
  const result=a.api.submit('s',1,{q:'A'});a.setSessionBlocked(true)
  pending.resolve(Response.json({attempt:{id:'should-not-delete-old-draft'}}))
  await assert.rejects(result,e=>e.code==='session_changed')
})
test('review 1: cross-tab signal preserves old content and requires guarded reconciliation',async()=>{
  const s=await state({session:async()=>({user:{id:'new',email:'new@example.test'}})})
  s.user.value={id:'old',email:'old@example.test'}
  const reasons=[];let allow=false
  s.registerIdentityGuard(reason=>{reasons.push(reason);return reason==='preserve'||allow})
  s.handleSessionSignal({key:'examhub:session-change',newValue:JSON.stringify({id:'new',registered:true})})
  assert.equal(s.sessionFrozen.value,true);assert.equal(s.user.value.id,'old');assert.deepEqual(reasons,['preserve'])
  await s.reconcileSession();assert.equal(s.user.value.id,'old');assert.equal(s.sessionFrozen.value,true)
  allow=true;await s.reconcileSession();assert.equal(s.user.value.id,'new');assert.equal(s.sessionFrozen.value,false)
})
test('review 1: focus reconciliation detects changes even when no storage signal arrived',async()=>{
  const s=await state({session:async()=>({user:{id:'new',email:null}})})
  s.user.value={id:'old',email:null};await s.checkSession()
  assert.equal(s.sessionFrozen.value,true);assert.equal(s.user.value.id,'old')
})
test('review 2: dirty identity guard runs before the old-identity auth request',async()=>{
  globalThis.localStorage=storage();const events=[]
  const s=await state({}, {migrateGuestDrafts:(from,to)=>{events.push(`migrate:${from.id}:${to.id}`);return 0}})
  s.user.value={id:'guest',email:null};let approved=false
  s.registerIdentityGuard(reason=>{events.push(`guard:${reason}`);return approved})
  const login=async()=>{events.push(`request:${s.user.value.id}`);return {user:{id:'account',email:'a@example.test'}}}
  assert.equal(await s.changeIdentity(login),false);assert.deepEqual(events,['guard:confirm'])
  approved=true;assert.equal(await s.changeIdentity(login),true)
  assert.deepEqual(events,['guard:confirm','guard:confirm','request:guest','migrate:guest:account']);assert.equal(s.user.value.id,'account')
})
test('review 2: editor guard saves recovery before authorizing remount and refuses cancellation',async()=>{
  let guard
  const e=await editor({}, {registerIdentityGuard:g=>{guard=g;return no}})
  globalThis.window.confirm=()=>false
  assert.equal(guard('confirm'),false);assert.equal(localStorage.length,0)
  globalThis.window.confirm=()=>true
  assert.equal(guard('confirm'),true)
  assert.equal(JSON.parse(localStorage.getItem('examhub:editor:u:set')).form.title,'before')
  e.form.value.title='cross-tab change';assert.equal(guard('preserve'),true)
  assert.equal(JSON.parse(localStorage.getItem('examhub:editor:u:set')).form.title,'cross-tab change')
})
test('review 2: storage failure prevents identity remount instead of silently losing editor content',async()=>{
  let guard;const e=await editor({}, {registerIdentityGuard:g=>{guard=g;return no}})
  localStorage.setItem=()=>{throw new Error('Quota')}
  assert.equal(guard('confirm'),false);assert.equal(e.form.value.title,'before')
})
test('review 3: a clean save navigates and the current draft becomes clean',async()=>{
  const e=await editor({save:async()=>({set:{id:'set',version:2}})})
  await e.save();assert.equal(e.dirty.value,false);assert.deepEqual(e.pushes,['/sets/set'])
})
test('review 3: second save after a pending-edit race updates the same set at its new version',async()=>{
  const pending=deferred(),requests=[]
  const e=await editor({save:(data,id)=>{requests.push({data:structuredClone(data),id});return requests.length===1?pending.promise:Promise.resolve({set:{id:'set',version:3}})}})
  const first=e.save();e.form.value.title='newer';pending.resolve({set:{id:'set',version:2}});await first
  await e.save();assert.equal(requests[1].id,'set');assert.equal(requests[1].data.version,2);assert.equal(requests[1].data.title,'newer');assert.equal(e.dirty.value,false)
})
test('review 5: guest answer migration merges only missing answers and retains both originals',async()=>{
  globalThis.localStorage=storage();const d=await script('lib/drafts.ts',{},['migrateGuestDrafts'])
  localStorage.setItem('examhub:answers:g:s:1',JSON.stringify({q1:'guest',q2:'guest-only'}))
  localStorage.setItem('examhub:answers:a:s:1',JSON.stringify({q1:'account'}))
  assert.equal(d.migrateGuestDrafts({id:'g',email:null},{id:'a',email:'a@x.test'}),1)
  assert.deepEqual(JSON.parse(localStorage.getItem('examhub:answers:a:s:1')),{q1:'account',q2:'guest-only'})
  assert.deepEqual(JSON.parse(localStorage.getItem('examhub:answers:g:s:1')),{q1:'guest',q2:'guest-only'})
})
test('review 5: registered-account drafts and jobs never migrate to a different account',async()=>{
  globalThis.localStorage=storage();const d=await script('lib/drafts.ts',{},['migrateGuestDrafts'])
  localStorage.setItem('examhub:answers:a:s:1','{"q":"private"}');localStorage.setItem('examhub:ai-job:a','job-a')
  d.migrateGuestDrafts({id:'a',email:'a@x.test'},{id:'b',email:'b@x.test'})
  assert.equal(localStorage.getItem('examhub:answers:b:s:1'),null);assert.equal(localStorage.getItem('examhub:ai-job:b'),null)
})
test('guest AI job pointer and editor recovery migrate, destination job wins on collision',async()=>{
  globalThis.localStorage=storage();const d=await script('lib/drafts.ts',{},['migrateGuestDrafts'])
  localStorage.setItem('examhub:ai-job:g','guest-job');localStorage.setItem('examhub:editor:g:new','editor')
  const from={id:'g',email:null},to={id:'a',email:'a@x.test'}
  d.migrateGuestDrafts(from,to);assert.equal(localStorage.getItem('examhub:ai-job:a'),'guest-job');assert.equal(localStorage.getItem('examhub:editor:a:new'),'editor')
  localStorage.setItem('examhub:ai-job:a','account-job');d.migrateGuestDrafts(from,to)
  assert.equal(localStorage.getItem('examhub:ai-job:a'),'account-job');assert.equal(localStorage.getItem('examhub:ai-job:g'),'guest-job')
})
test('review 6: disposed AI component cannot consume a late completed response',async()=>{
  globalThis.localStorage=storage();const pending=deferred(),dispose=[]
  const a=await script('components/AIGenerator.vue',{defineProps:()=>({}),defineEmits:()=>no,api:{job:()=>pending.promise},message:e=>e.message,user:ref({id:'u'}),onBeforeUnmount:f=>dispose.push(f)},['job','poll'])
  a.job.value={id:'old',status:'running'};const poll=a.poll();dispose.forEach(f=>f());pending.resolve({job:{id:'old',status:'completed'}});await poll
  assert.equal(a.job.value.status,'running')
})

for(const shortOnly of [false,true]){
  for(const path of ['components/AttemptResult.vue','views/HistoryView.vue','views/CollectionView.vue']){
    test(`review 4: ${path} renders ${shortOnly?'no automatic score for all-short':'1 / 1 for mixed'} attempts`,async()=>{
      globalThis.localStorage=storage()
      const {renderView}=await import('./harness.mjs')
      const scoring=await script('lib/scoring.ts',{},['automaticScore','scoreLabel'])
      const results=[{...question,type:'short',correct:null,userAnswer:'my text',questionId:'short'}]
      if(!shortOnly)results.unshift({...question,correct:true,userAnswer:'A',questionId:'single'})
      const attempt={id:'attempt',setId:'s',setTitle:'Test set',createdAt:'2026-10-20',version:1,total:results.length,correct:shortOnly?0:1,results}
      const bindings={...scoring,defineProps:()=>({attempt}),attempt,useRoute:()=>({path:'/',query:{}}),api:{},date:()=>'',message:e=>e.message,user:ref({id:'u',name:'访客'}),authOpen:ref(false),draftKey:()=>'',visibilityLabels:{}}
      const names=path.includes('AttemptResult')?['results','score','shortCount','onlyWrong']:path.includes('History')?['attempts','selected','loading','error','wrongOnly','visible','active']:['home','library','sets','attempts','loading','error','q','topic','scope','topics','filtered','featured','resumed']
      const html=await renderView(path,bindings,names,vm=>{if(vm.attempts)vm.attempts.value=[attempt];if(vm.loading)vm.loading.value=false})
      const text=html.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ')
      if(shortOnly){assert.match(text,/无单选题/);assert.doesNotMatch(text,/0\s*\/\s*1/)}
      else{assert.match(text,/1\s*\/\s*1/);assert.doesNotMatch(text,/1\s*\/\s*2/)}
    })
  }
}

test('review 7: drawer moves/traps focus, excludes background, handles global Escape and restores opener',async()=>{
  const originalDocument=globalThis.document
  const listeners=new Map(),background={inert:false}
  const doc={activeElement:null,body:{style:{overflow:'auto'}},addEventListener:(type,handler)=>listeners.set(type,handler),removeEventListener:type=>listeners.delete(type)}
  const element=()=>({isConnected:true,hidden:false,focus(){doc.activeElement=this}})
  const opener=element(),first=element(),last=element(),outside=element()
  const panel={querySelectorAll:()=>[first,last],contains:el=>[first,last].includes(el),focus(){doc.activeElement=this}}
  globalThis.document=doc;opener.focus()
  try{
    const {activateDrawer}=await script('lib/drawer.ts',{},['activateDrawer'])
    let closed=0
    const release=activateDrawer(panel,background,()=>{closed++;release()})
    assert.equal(doc.activeElement,first);assert.equal(background.inert,true);assert.equal(doc.body.style.overflow,'hidden')
    const key=(key,shiftKey=false)=>{let prevented=false;listeners.get('keydown')({key,shiftKey,preventDefault:()=>prevented=true,stopPropagation:no});return prevented}
    last.focus();assert.equal(key('Tab'),true);assert.equal(doc.activeElement,first)
    first.focus();assert.equal(key('Tab',true),true);assert.equal(doc.activeElement,last)
    outside.focus();listeners.get('focusin')({target:outside});assert.equal(doc.activeElement,first)
    outside.focus();key('Escape');assert.equal(closed,1);assert.equal(background.inert,false);assert.equal(doc.activeElement,opener);assert.equal(doc.body.style.overflow,'auto');assert.equal(listeners.size,0)
  }finally{globalThis.document=originalDocument}
})

test('review 1: identity conflict preserves actual practice draft and never shows version-reload action',async()=>{
  globalThis.localStorage=storage();globalThis.window={scrollTo:no}
  const drafts=await script('lib/drafts.ts',{},['draftKey','readDraft','writeDraft'])
  const apiModule=await script('lib/api.ts',{},['ApiError'])
  const api={practice:async()=>({set:{id:'set',version:1},questions:[question]}),submit:async()=>{throw new apiModule.ApiError('Identity changed',409,'session_changed')}}
  const p=await script('views/PracticeView.vue',{...drafts,api,ApiError:apiModule.ApiError,useRoute:()=>({params:{id:'set'}}),user:ref({id:'old'}),message:e=>e.message,registerIdentityGuard:()=>no,notify:no},['load','answers','submit','conflict','attempt'])
  await p.load();p.answers.value.q='A';await p.submit()
  assert.equal(localStorage.getItem('examhub:answers:old:set:1'),'{"q":"A"}');assert.equal(p.conflict.value,false);assert.equal(p.attempt.value,undefined)
})

test('explicit reload ignores stale recovery and removes it only after successful server read',async()=>{
  let calls=0
  const set={id:'set',isOwner:true,title:'latest',description:'',topic:'',visibility:'private',version:9,questions:[question]}
  const e=await editor({set:async()=>{calls++;return {set}}})
  localStorage.setItem('examhub:editor:u:set',JSON.stringify({form:{...set,title:'stale',version:1},targetId:'set'}))
  window.confirm=()=>false;await e.reload();assert.equal(calls,0);assert.ok(localStorage.getItem('examhub:editor:u:set'))
  window.confirm=()=>true;await e.reload();assert.equal(calls,1);assert.equal(e.form.value.title,'latest');assert.equal(e.form.value.version,9);assert.equal(localStorage.getItem('examhub:editor:u:set'),null);assert.equal(e.dirty.value,false)
})
test('failed explicit reload retains the recovery copy and current unsaved form',async()=>{
  const e=await editor({set:async()=>{throw new Error('offline')}})
  localStorage.setItem('examhub:editor:u:set','recovery')
  await e.reload();assert.equal(localStorage.getItem('examhub:editor:u:set'),'recovery');assert.equal(e.form.value.title,'before')
})
test('successful auth keeps route in place instead of issuing a second dirty-route navigation',async()=>{
  const navigations=[],current=ref({id:'guest',email:null}),open=ref(true)
  const a=await script('components/AuthDialog.vue',{useRouter:()=>({push:async route=>navigations.push(route)}),api:{auth:async()=>({user:{id:'account'}})},authOpen:open,user:current,notify:no,message:e=>e.message,changeIdentity:async operation=>{current.value=(await operation()).user;return true}},['submit'])
  await a.submit();assert.equal(current.value.id,'account');assert.equal(open.value,false);assert.deepEqual(navigations,[])
})
