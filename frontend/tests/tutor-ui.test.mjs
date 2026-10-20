import {test,afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {ref} from 'vue'
import {script,storage,deferred,renderView} from './harness.mjs'
const original={storage:globalThis.localStorage,window:globalThis.window,fetch:globalThis.fetch}
afterEach(()=>{globalThis.localStorage=original.storage;globalThis.window=original.window;globalThis.fetch=original.fetch})
const no=()=>{},request=()=>{},helpers=await script('lib/tutorRequests.ts',{},['createTutorRequest','createTutorReader'])
const contract=await script('lib/tutor.ts',{request},['tutorMode','tutorStatus','tutorToolLabel','benchmarkValue'])
const docs=await script('lib/documents.ts',{},['percent'])
const question={id:'q',type:'single',prompt:'你如何区分两个概念',options:['甲','乙'],topic:'概念'}
const session={id:'S',setId:'set',setTitle:'测试教材题集',setVersion:2,version:4,goal:'解释理由',mode:'rule',status:'waiting',busy:false,maxQuestions:2,turnId:1,pending:{kind:'question',questionId:'q',prompt:question.prompt},currentQuestion:question,asked:['q'],answers:[],events:[],trace:[],summary:{answered:0,correct:0,objectiveTotal:0,followups:0},modelCalls:0,elapsedMs:0,budget:{maxModelCalls:32,maxModelCallsPerTurn:6,maxRuleStepsPerTurn:12,remainingModelCalls:32}}
function env(tutorApi){globalThis.localStorage=storage();globalThis.window={confirm:()=>true};return {...helpers,...contract,tutorApi,api:{config:async()=>({configured:false})},useRoute:()=>({params:{id:'S'}}),user:ref({id:'U'}),sessionFrozen:ref(false),identityChanging:ref(false),registerIdentityGuard:()=>no,notify:no,message:e=>e.message,downloadJSON:no}}
const names=['session','answer','pendingRequest','busy','loading','error','storageError','config','conflict','waiting','canAnswer','isSingle','applySession','load','command','retry','discard']
test('session command 409 loads latest version, preserves old answer and never resubmits',async()=>{
 const requests=[];let reads=0
 const vm=await script('views/TutorSessionView.vue',env({command:async(id,body)=>{requests.push(body);throw Object.assign(new Error('教学进度已更新'),{status:409})},session:async()=>{reads++;return {session:{...session,version:7,turnId:2,pending:{kind:'followup',questionId:'q',prompt:'为什么'}}}}}),names)
 vm.applySession(session);vm.answer.value='甲';await vm.command('answer')
 assert.equal(requests.length,1);assert.equal(requests[0].version,4);assert.equal(requests[0].turnId,1);assert.equal(reads,1)
 assert.equal(vm.session.value.version,7);assert.equal(vm.pendingRequest.value.blocked,true);assert.equal(vm.conflict.value,true)
 assert.equal(localStorage.getItem('examhub:tutor:answer:U:S:1'),'甲');assert.equal(vm.answer.value,'')
 await vm.retry();assert.equal(requests.length,1)
})
test('session waiting UI reveals no references, has real empty objective state and no invented progress',async()=>{
 const html=await renderView('views/TutorSessionView.vue',env({}),names,vm=>vm.applySession(session))
 assert.match(html,/你如何区分两个概念/);assert.match(html,/暂无单选作答/);assert.match(html,/实际模型调用/)
 assert.doesNotMatch(html,/参考答案|掌握率|排名|0%/)
})
test('interrupted elapsed time is explicitly incomplete and followup always renders free text',async()=>{
 const value={...session,mode:'agent',elapsedMs:2100,timingIncomplete:true,pending:{kind:'followup',questionId:'q',prompt:'为什么选择甲'}}
 const html=await renderView('views/TutorSessionView.vue',env({}),names,vm=>vm.applySession(value))
 assert.match(html,/计时不完整/);assert.doesNotMatch(html,/2.10 秒/);assert.match(html,/<textarea/);assert.doesNotMatch(html,/type="radio"/)
})
test('transcript renders submitted short answer as self review and source-only evidence honestly',async()=>{
 const events=[{id:'a',type:'answer',result:{kind:'question',prompt:'说明理由',userAnswer:'我的解释',correct:null,type:'short',answer:'参考解释'}},{id:'f',type:'feedback',message:'建议对照资料',evidence:[{evidenceId:'E',quote:'教材摘录',citation:null}]}]
 const html=await renderView('components/TutorTranscript.vue',{defineProps:()=>({events}),events},['entries'])
 assert.match(html,/不计入自动得分/);assert.match(html,/无 PDF 原页核验/);assert.match(html,/教材摘录/);assert.match(html,/参考解释/)
})
test('tutor API uses encoded owner-scoped routes and existing expected-user protection',async()=>{
 const client=await script('lib/api.ts',{},['request','setExpectedUser']);client.setExpectedUser('U')
 const {tutorApi}=await script('lib/tutor.ts',{request:client.request},['tutorApi']);const calls=[]
 globalThis.fetch=async(url,options)=>{calls.push({url,...options});return Response.json({session})}
 await tutorApi.command('S/1',{type:'answer',requestId:'stable-token-12345',version:4,turnId:1,answer:'甲'})
 assert.equal(calls[0].url,'/api/tutor/sessions/S%2F1/commands');assert.equal(calls[0].headers['X-Expected-User'],'U');assert.equal(JSON.parse(calls[0].body).requestId,'stable-token-12345')
})
test('guest tutor drafts and pending tokens migrate only guest to account, keeping originals and destination',async()=>{
 globalThis.localStorage=storage();const {migrateGuestDrafts}=await script('lib/drafts.ts',{},['migrateGuestDrafts'])
 localStorage.setItem('examhub:tutor:answer:G:S:1','guest');localStorage.setItem('examhub:tutor:answer:U:S:1','account');localStorage.setItem('examhub:tutor:command:G:S','pending-token');localStorage.setItem('examhub:tutor:create:G','create-token')
 migrateGuestDrafts({id:'G',email:null},{id:'U',email:'user@example.test'})
 assert.equal(localStorage.getItem('examhub:tutor:answer:U:S:1'),'account');assert.equal(localStorage.getItem('examhub:tutor:command:U:S'),'pending-token');assert.equal(localStorage.getItem('examhub:tutor:create:U'),'create-token');assert.equal(localStorage.getItem('examhub:tutor:answer:G:S:1'),'guest')
 migrateGuestDrafts({id:'U',email:'user@example.test'},{id:'V',email:'v@example.test'});assert.equal(localStorage.getItem('examhub:tutor:command:V:S'),null)
})
test('teaching benchmark renders failed expectations, observed values and controlled-strategy scope',async()=>{
 const report={caseCount:1,version:'v1',datasetId:'fixture',datasetVersion:'1',datasetHash:'hash',createdAt:'now',limitations:['不是学习效果'],strategies:[{name:'scripted-agent',summary:{passedChecks:0,checks:1,passRate:0,passedCases:0,cases:1,errorCases:0},cases:[{id:'case',title:'拒绝伪引用',goal:'核验边界',passed:false,error:null,checks:[{code:'reject',message:'保持拒绝状态',expected:true,observed:false,passed:false}],actualTrace:[]}]}]}
 const html=await renderView('components/TutorBenchmark.vue',{tutorApi:{},sessionFrozen:ref(false),...contract,...docs},['report','busy','error','operations','outcomes'],vm=>vm.report.value=report)
 assert.match(html,/受控工具策略 · 离线/);assert.match(html,/未通过/);assert.match(html,/预期：是/);assert.match(html,/观察：否/);assert.match(html,/0 \/ 1/);assert.match(html,/不是学习效果/)
})
test('rule setup needs no key, deduplicates sets and only creates after explicit action',async()=>{
 globalThis.localStorage=storage();let creates=0;const navigations=[]
 const set={id:'set',title:'集合',version:1,questionCount:2}
 const bindings={...helpers,...contract,useRoute:()=>({query:{}}),useRouter:()=>({push:path=>navigations.push(path)}),user:ref({id:'U'}),sessionFrozen:ref(false),identityChanging:ref(false),registerIdentityGuard:()=>no,notify:no,message:e=>e.message,api:{sets:async()=>({sets:[set]}),config:async()=>({configured:false})},tutorApi:{create:async body=>{creates++;assert.equal(body.mode,'rule');assert.equal(JSON.parse(localStorage.getItem('examhub:tutor:create:U')).operation.body.requestId,body.requestId);return {session}}}}
 const vm=await script('views/TutorSetupView.vue',bindings,['load','sets','goal','maxQuestions','mode','valid','start'])
 await vm.load();assert.equal(vm.sets.value.length,1);assert.equal(creates,0)
 vm.goal.value='说明两个概念的差异';vm.maxQuestions.value=1;assert.equal(vm.valid.value,true);await vm.start()
 assert.equal(creates,1);assert.deepEqual(navigations,['/tutor/S'])
})
