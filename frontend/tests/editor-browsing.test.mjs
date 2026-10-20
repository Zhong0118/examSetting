import {test,afterEach} from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import ts from 'typescript'
import * as Vue from 'vue'
import * as server from 'vue/server-renderer'
import {parse,compileTemplate} from 'vue/compiler-sfc'
import {script,storage,deferred} from './harness.mjs'

const path='views/EditorView.vue',no=()=>{}
const original={window:globalThis.window,storage:globalThis.localStorage}
afterEach(()=>{globalThis.window=original.window;globalThis.localStorage=original.storage})
const names=['route','editing','form','canEdit','loading','save','error','conflict','dirty','busy','search','questionType','questionTopic','topics','page','pageSize','currentPage','pageQuestions','filteredQuestions','activeQuestion','changePage','showQuestion','removeQuestion','add','importQuestions','citationQuestion','bindCitation','restoreEditor','preserveEditor','quality','qualityBusy','qualityError','qualityStale','initialSelection','initialDocumentId']
const browser=await script('lib/question-browser.ts',{},['filterQuestions'])
const question=i=>({id:`q${i}`,type:'single',prompt:`题目 ${i}`,options:[`正确 ${i}`,`错误 ${i}`],answer:`正确 ${i}`,explanation:'解析',source:'原文',topic:i%2?'网络':'系统'})
async function editor(count=100,api={}){
  globalThis.localStorage=storage();globalThis.window={confirm:()=>true,addEventListener:no,removeEventListener:no}
  const requests=[],pushes=[],notices=[];let guard
  const bindings={...browser,useRoute:()=>({params:{id:'set'},query:{}}),useRouter:()=>({push:async p=>pushes.push(p)}),api:{save:async(data,id)=>{requests.push({data,id});return {set:{id:'set',version:2}}},...api},ApiError:Error,message:e=>e.message,notify:m=>notices.push(m),user:Vue.ref({id:'u'}),registerIdentityGuard:g=>{guard=g;return no}}
  const vm=await script(path,bindings,names)
  vm.form.value={title:'题集',description:'简介',topic:'课程',visibility:'private',version:1,questions:Array.from({length:count},(_,i)=>question(i+1))}
  vm.canEdit.value=true;vm.loading.value=false
  return {...vm,bindings,requests,pushes,notices,guard:reason=>guard(reason)}
}

// Compile and render the real template against the same reactive editor used by each test.
const source=await readFile(new URL('../src/views/EditorView.vue',import.meta.url),'utf8')
const {code,errors}=compileTemplate({source:parse(source).descriptor.template.content,filename:path,id:'editor-browsing',ssr:true,ssrCssVars:[]})
assert.deepEqual(errors,[])
const executable=code.replace(/import \{([^}]+)\} from "([^"]+)"/g,(_,names,module)=>`const {${names.replace(/\bas\b/g,':')}} = ${module==='vue'?'Vue':'server'}`).replace('export function','function')
const ssrRender=new Function('Vue','server',`${ts.transpileModule(executable,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText};return ssrRender`)(Vue,server)
async function render(e){
  const app=Vue.createSSRApp({setup:()=>({...e.bindings,...e}),ssrRender})
  app.component('RouterLink',{setup:(_,ctx)=>()=>Vue.h('a',null,ctx.slots.default?.())})
  for(const name of ['Icon','AIGenerator','CitationPicker','CitationCard','QualityPanel','Pagination'])app.component(name,{render:()=>null})
  return server.renderToString(app)
}

test('100 questions render ten directory entries and only one complete editor',async()=>{
  const e=await editor(),html=await render(e)
  assert.equal((html.match(/aria-label="编辑第 \d+ 题"/g)||[]).length,10)
  assert.equal((html.match(/placeholder="写下一个清晰的问题"/g)||[]).length,1)
  assert.equal((html.match(/<form\b[^>]*\bnovalidate/g)||[]).length,1)
  assert.equal(e.form.value.questions.length,100)
})

test('saving validates an off-page question and opens its original page before any request',async()=>{
  const e=await editor();e.form.value.questions[99].prompt=' '
  await e.save()
  assert.equal(e.requests.length,0);assert.match(e.error.value,/第 100 题.*题干/)
  assert.equal(e.currentPage?.value,10)
  assert.equal(e.activeQuestion?.value,e.form.value.questions[99])
  const html=await render(e)
  assert.match(html,/删除第 100 题/)
  assert.equal((html.match(/placeholder="写下一个清晰的问题"/g)||[]).length,1)
})

test('JS validation rejects an empty title instead of relying on native validation',async()=>{
  const e=await editor(1);e.form.value.title=' '
  await e.save()
  assert.equal(e.requests.length,0);assert.match(e.error.value,/题集名称/)
})

test('search covers options and topics, combines filters and retains original numbers',async()=>{
  const e=await editor();e.changePage(8);e.search.value='错误 98'
  assert.equal(e.currentPage.value,1);assert.deepEqual(e.pageQuestions.value.map(x=>x.index),[97])
  e.search.value='网络';e.questionType.value='single';e.questionTopic.value='网络'
  assert.equal(e.filteredQuestions.value.length,50)
  assert.deepEqual(e.pageQuestions.value.map(x=>x.index),[0,2,4,6,8,10,12,14,16,18])
  assert.ok(e.topics.value.includes('系统'));assert.ok(e.topics.value.includes('网络'))
  const html=await render(e);assert.match(html,/第 19 题/);assert.doesNotMatch(html,/第 20 题/)
  e.search.value='不存在的题干';assert.equal(e.pageQuestions.value.length,0)
  assert.match(await render(e),/没有匹配/)
  assert.equal(e.form.value.questions.length,100)
})

test('paging, collapsing and filtering retain original edits, selected answer and citation in save and draft',async()=>{
  const e=await editor(),questions=e.form.value.questions,first=questions[0],last=questions[99]
  assert.equal(e.pageQuestions.value[0].question,first)
  first.prompt='修改后的题干';first.options[0]='修改后的正确选项';first.answer=first.options[0]
  e.citationQuestion.value=first
  e.changePage(10);e.search.value='题目 100';e.questionType.value='single';e.questionTopic.value='系统'
  const citation={documentId:'D',documentTitle:'教材',documentHash:'hash',page:3,quote:'绑定的教材原文'}
  e.bindCitation(citation);last.explanation='折叠期间的修改'
  e.activeQuestion.value=undefined
  e.showQuestion(0)
  assert.equal(e.form.value.questions,questions);assert.equal(e.activeQuestion.value,first)
  assert.equal(e.pageQuestions.value[0].question,first);assert.equal(first.citation.quote,citation.quote)
  assert.equal(first.source,citation.quote);assert.equal(first.answer,'修改后的正确选项')
  assert.equal(last.explanation,'折叠期间的修改')
  assert.equal(e.guard('preserve'),true)
  const draft=JSON.parse(localStorage.getItem('examhub:editor:u:set')).form
  assert.equal(draft.questions.length,100);assert.equal(draft.questions[0].prompt,'修改后的题干')
  assert.deepEqual(draft.questions[0].citation,citation);assert.equal(draft.questions[99].explanation,'折叠期间的修改')
  await e.save()
  assert.equal(e.requests[0].data.questions.length,100)
  assert.deepEqual(e.requests[0].data.questions[0],draft.questions[0]);assert.equal(e.dirty.value,false)
})

for(const [label,change,expected] of [
  ['prompt',q=>q.prompt='',/题干/],
  ['empty option',q=>q.options[1]=' ',/选项/],
  ['duplicate option',q=>q.options[1]=q.options[0],/重复/],
  ['unselected answer',q=>q.answer='other',/正确答案/],
  ['short answer',q=>{q.type='short';q.options=[];q.answer=' '},/参考答案/],
  ['long prompt',q=>q.prompt='x'.repeat(10001),/题干/],
  ['long option',q=>q.options[1]='x'.repeat(2001),/选项/],
  ['long explanation',q=>q.explanation='x'.repeat(20001),/解析/],
  ['long source',q=>q.source='x'.repeat(20001),/出处/],
  ['long topic',q=>q.topic='x'.repeat(20001),/知识点/],
  ['long answer',q=>{q.type='short';q.options=[];q.answer='x'.repeat(20001)},/答案/],
])test(`filtered or collapsed invalid ${label} blocks save and reveals the original question`,async()=>{
  const e=await editor(),invalid=e.form.value.questions[56];change(invalid)
  e.search.value='题目 2';e.questionType.value='single';e.questionTopic.value='系统';e.changePage(2)
  assert.ok(!e.pageQuestions.value.some(x=>x.question===invalid))
  await e.save()
  assert.equal(e.requests.length,0);assert.match(e.error.value,/第 57 题/);assert.match(e.error.value,expected)
  assert.equal(e.search.value,'');assert.equal(e.questionType.value,'');assert.equal(e.questionTopic.value,'')
  assert.equal(e.currentPage.value,6);assert.equal(e.activeQuestion.value,invalid)
  assert.match(await render(e),/删除第 57 题/)
})

test('a collapsed invalid question on the current page is expanded on save',async()=>{
  const e=await editor(10);e.form.value.questions[4].answer=''
  e.activeQuestion.value=undefined
  assert.equal((await render(e)).includes('写下一个清晰的问题'),false)
  await e.save();assert.equal(e.requests.length,0)
  assert.equal(e.currentPage.value,1);assert.equal(e.activeQuestion.value,e.form.value.questions[4])
  assert.match(await render(e),/删除第 5 题/)
})

for(const [key,value] of [['title','x'.repeat(201)],['description','x'.repeat(2001)],['topic','x'.repeat(81)]])test(`JS validates the existing ${key} length limit`,async()=>{
  const e=await editor(1);e.form.value[key]=value;await e.save()
  assert.equal(e.requests.length,0);assert.ok(e.error.value)
})

test('add and import reveal the new question, clear filters and keep the entire batch',async()=>{
  const e=await editor(97);e.search.value='题目 1';e.questionTopic.value='网络';e.questionType.value='single'
  e.add('short')
  assert.equal(e.form.value.questions.length,98);assert.equal(e.currentPage.value,10)
  assert.equal(e.activeQuestion.value,e.form.value.questions[97]);assert.equal(e.activeQuestion.value.type,'short')
  assert.equal(e.search.value,'');assert.equal(e.questionType.value,'');assert.equal(e.questionTopic.value,'')
  const imported=[question(99),question(100)];e.search.value='没有结果';e.importQuestions(imported)
  assert.equal(e.form.value.questions.length,100);assert.equal(e.activeQuestion.value,e.form.value.questions[98])
  assert.equal(e.activeQuestion.value.id,'q99');assert.equal(e.currentPage.value,10)
  e.add('single');assert.equal(e.form.value.questions.length,100);assert.match(e.error.value,/100/)
  e.importQuestions([question(101)]);assert.equal(e.form.value.questions.length,100);assert.match(e.error.value,/100/)
  const html=await render(e);assert.match(html,/最多 100/)
  assert.match(html,/<button[^>]*disabled[^>]*>[\s\S]*?添加单选题/)
})

test('an import exceeding the remaining capacity is rejected whole without silent truncation',async()=>{
  const e=await editor(99),questions=e.form.value.questions,last=questions[98]
  e.importQuestions([question(100),question(101)])
  assert.equal(e.form.value.questions,questions);assert.equal(questions.length,99);assert.equal(questions[98],last)
  assert.match(e.error.value,/100/);assert.match(e.error.value,/2/)
  assert.ok(!e.notices.some(x=>x.includes('已导入')))
})

test('a rejected AI import remains recoverable and can be retried after freeing capacity',async()=>{
  const e=await editor(99)
  const generator=await script('components/AIGenerator.vue',{
    defineProps:()=>({title:'题集',topic:'课程'}),
    defineEmits:()=> (_event,...args)=>e.importQuestions(...args),
    user:Vue.ref({id:'u'}),api:{},message:e=>e.message
  },['job','importQuestions','imported'])
  generator.job.value={id:'saved-job',status:'completed',questions:[question(100),question(101)]}
  localStorage.setItem('examhub:ai-job:u','saved-job')
  generator.importQuestions()
  assert.equal(generator.imported.value,false)
  assert.equal(localStorage.getItem('examhub:ai-job:u'),'saved-job')
  e.removeQuestion(0)
  generator.importQuestions()
  assert.equal(generator.imported.value,true)
  assert.equal(e.form.value.questions.length,100)
  assert.equal(localStorage.getItem('examhub:ai-job:u'),null)
})

test('editing the matching text keeps the selected editor mounted until a new filter is chosen',async()=>{
  const e=await editor(2)
  e.search.value='题目 1'
  const first=e.form.value.questions[0]
  e.activeQuestion.value=first
  first.prompt='重新编写题干'
  assert.equal(e.pageQuestions.value[0]?.question,first)
  assert.match(await render(e),/placeholder="写下一个清晰的问题"/)
  e.search.value='不存在的新筛选'
  assert.equal(e.pageQuestions.value.length,0)
  assert.equal(e.form.value.questions[0].prompt,'重新编写题干')
})

test('deleting the active last-page question opens a reasonable neighbour and preserves other edits',async()=>{
  const e=await editor(11),first=e.form.value.questions[0],previous=e.form.value.questions[9]
  first.prompt='保留的修改';e.showQuestion(10);e.removeQuestion(10)
  assert.equal(e.currentPage.value,1);assert.equal(e.activeQuestion.value,previous)
  assert.equal(e.form.value.questions[0],first);assert.equal(first.prompt,'保留的修改')
  e.showQuestion(0);const next=e.form.value.questions[1];e.removeQuestion(0)
  assert.equal(e.activeQuestion.value,next)
  while(e.form.value.questions.length)e.removeQuestion(0)
  assert.equal(e.currentPage.value,1);assert.equal(e.activeQuestion.value,undefined)
  await e.save();assert.equal(e.requests.length,0);assert.match(e.error.value,/至少/)
})

test('paging during an in-flight save preserves the submitted snapshot and later hidden edits',async()=>{
  const pending=deferred(),requests=[]
  const e=await editor(100,{save:(data,id)=>{requests.push({data,id});return pending.promise}})
  const saving=e.save();e.changePage(10);e.form.value.questions[0].prompt='提交后的修改'
  await e.save();assert.equal(requests.length,1)
  pending.resolve({set:{id:'set',version:2}});await saving
  assert.equal(requests[0].data.questions[0].prompt,'题目 1')
  assert.equal(e.dirty.value,true);assert.equal(e.form.value.version,2);assert.deepEqual(e.pushes,[])
  assert.equal(JSON.parse(localStorage.getItem('examhub:editor:u:set')).form.questions[0].prompt,'提交后的修改')
})
