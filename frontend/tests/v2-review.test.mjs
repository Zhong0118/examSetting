import {test} from 'node:test'
import assert from 'node:assert/strict'
import {createRequire} from 'node:module'
import {script,deferred,storage} from './harness.mjs'
const require=createRequire(new URL('../package.json',import.meta.url))
const {ref,reactive,nextTick}=require('vue')
const no=()=>{},message=e=>e.message
const docs=await script('lib/documents.ts',{},['highlightQuote','normalizeQuote'])
const doc=(id,pageCount=2)=>({id,title:id,pageCount,sha256:id,warnings:[]})
const pages=[{page:1,text:'Alpha original page long enough',charCount:31},{page:2,text:'Beta second page quotation text',charCount:31}]
test('reader actually updates current text and highlight from reactive query changes',async()=>{
 const route=reactive({params:{id:'A'},query:{page:'1',quote:'Alpha'}})
 const reader=await script('views/DocumentReaderView.vue',{useRoute:()=>route,useRouter:()=>({replace:async({query})=>{route.query=query}}),api:{document:async()=>({document:doc('A'),pages})},...docs,selectionError:()=>'',message},['load','setPage','page','current','chunks'])
 await reader.load();assert.equal(reader.current.value.page,1);assert.equal(reader.chunks.value.find(x=>x.highlight).text,'Alpha')
 route.query={page:'2',quote:'second page'};await nextTick()
 assert.equal(reader.page.value,2);assert.equal(reader.current.value.text,pages[1].text);assert.equal(reader.chunks.value.find(x=>x.highlight).text,'second page')
 reader.setPage(1);await nextTick();assert.equal(route.query.page,1);assert.equal(reader.current.value.page,1)
})
test('disposed reader cannot rewrite a new document route',async()=>{
 const pending=deferred(),route=reactive({params:{id:'A'},query:{page:'1'}}),unmount=[],navigations=[]
 const reader=await script('views/DocumentReaderView.vue',{useRoute:()=>route,useRouter:()=>({replace:async value=>navigations.push({id:route.params.id,...value})}),api:{document:()=>pending.promise},...docs,selectionError:()=>'',message,onBeforeUnmount:fn=>unmount.push(fn)},['load'])
 const loading=reader.load();unmount.forEach(fn=>fn());route.params.id='B';route.query={page:'2',quote:'Beta'}
 pending.resolve({document:doc('A',1),pages:[pages[0]]});await loading
 assert.deepEqual(navigations,[])
})
test('NFKC combining character citation highlights original graphemes',()=>{
 const text='Cafe\u0301 example',quote='Café'
 assert.ok(docs.normalizeQuote(text).includes(docs.normalizeQuote(quote)))
 assert.equal(docs.highlightQuote(text,quote).some(x=>x.highlight),true)
 for(const [source,quote] of [['한글','한글'],['Cafe\u0301 example','Café']]){const chunks=docs.highlightQuote(source,quote);assert.ok(chunks.some(x=>x.highlight));assert.equal(chunks.map(x=>x.text).join(''),source)}
})
test('normal full-width, whitespace and astral quote highlighting preserves exact source',()=>{
 for(const [text,quote] of [['前😀Ａ\n B后','😀A B'],['x\n\nhello   world y','hello world']]){
  const out=docs.highlightQuote(text,quote);assert.equal(out.map(x=>x.text).join(''),text);assert.ok(out.some(x=>x.highlight))
 }
})
test('citation picker changes physical page, binds original quote and rejects wrong-page quote',async()=>{
 const props=reactive({open:false,initialDocumentId:'A'}),events=[]
 const picker=await script('components/CitationPicker.vue',{defineProps:()=>props,defineEmits:()=>((...e)=>events.push(e)),api:{document:async()=>({document:doc('A'),pages}),documents:async()=>({documents:[doc('A')]})},normalizeQuote:docs.normalizeQuote,message},['read','page','quote','valid','bind','documentId'])
 props.open=true;await nextTick();await new Promise(r=>setImmediate(r));await nextTick()
 picker.page.value=2;picker.quote.value='second page';assert.equal(picker.valid.value,true);picker.bind()
 assert.equal(events[0][0],'select');assert.equal(events[0][1].page,2);assert.equal(events[0][1].documentId,'A');assert.equal(events[0][1].quote,'second page')
 picker.page.value=1;assert.equal(picker.valid.value,false)
})
test('editor late quality result is stale after edits and bound quote is preserved in old-user draft',async()=>{
 globalThis.localStorage=storage();globalThis.window={confirm:()=>true};let guard;const pending=deferred()
 const vm=await script('views/EditorView.vue',{useRoute:()=>({params:{id:'S'},query:{}}),useRouter:()=>({}),api:{checkQuality:()=>pending.promise},message,notify:no,ApiError:Error,user:ref({id:'old'}),registerIdentityGuard:g=>{guard=g;return no}},['form','checkQuality','quality','qualityStale','citationQuestion','bindCitation'])
 vm.form.value.questions=[{id:'q',prompt:'before'}];vm.citationQuestion.value=vm.form.value.questions[0];vm.bindCitation({documentId:'A',page:2,quote:'second page',documentHash:'A',documentTitle:'A'})
 const run=vm.checkQuality();vm.form.value.questions[0].prompt='after';pending.resolve({report:{total:1}});await run
 assert.equal(vm.qualityStale.value,true);assert.equal(guard('preserve'),true)
 const saved=JSON.parse(localStorage.getItem('examhub:editor:old:S'));assert.equal(saved.form.questions[0].citation.page,2);assert.equal(saved.form.questions[0].source,'second page')
})
test('detail rejects report from newer version, reloads visible set and requires recheck',async()=>{
 const {filterQuestions}=await script('lib/question-browser.ts',{},['filterQuestions'])
 const question=id=>({id,type:'short',prompt:id,options:[],topic:'',source:''})
 const old={id:'S',version:1,questions:[question('old')]},latest={id:'S',version:2,questions:[question('new1'),question('new2')]},report={total:2,items:[]};let reads=0;const notices=[]
 const vm=await script('views/DetailView.vue',{filterQuestions,useRoute:()=>({params:{id:'S'}}),useRouter:()=>({}),api:{set:async()=>({set:reads++?latest:old}),setQuality:async()=>({report,version:2})},message,notify:m=>notices.push(m)},['load','checkQuality','set','quality'])
 await vm.load();await vm.checkQuality();assert.equal(vm.quality.value,undefined);assert.equal(vm.set.value.version,2);assert.equal(notices.length,1)
 await vm.checkQuality();assert.equal(vm.quality.value.total,2)
})
test('PDF blob uses same-origin credentials and rejects stale response after identity change',async()=>{
 const pending=deferred(),vm=await script('lib/api.ts',{},['api','setExpectedUser']);vm.setExpectedUser('A');let request
 globalThis.fetch=(url,init)=>{request={url,...init};return pending.promise}
 const loading=vm.api.documentFile('doc');vm.setExpectedUser('B');pending.resolve(new Response(new Blob(['PDF'])))
 await assert.rejects(loading,e=>e.code==='session_changed');assert.equal(request.credentials,'same-origin');assert.equal(request.url,'/api/documents/doc/file')
})
test('PdfCanvas loads authenticated bytes and renders actual new physical page on prop change',async()=>{
 const {readFile}=await import('node:fs/promises'),ts=require('typescript'),vue=require('vue')
 let source=await readFile(new URL('../src/components/PdfCanvas.vue',import.meta.url),'utf8')
 source=source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'').replace("import('../lib/pdf')",'Promise.resolve(pdfModule)')
 source+='\nreturn {load,canvas,container,busy,error}'
 const props=reactive({documentId:'A',page:1}),requested=[],rendered=[],disposed=[];let bytes
 const pdf={getPage:async n=>{requested.push(n);return {getViewport:({scale})=>({width:100*scale,height:200*scale}),render:opts=>{rendered.push({n,opts});return {promise:Promise.resolve(),cancel:no}}}},destroy:async()=>{}}
 const env={...vue,defineProps:()=>props,onMounted:no,onBeforeUnmount:fn=>disposed.push(fn),message,api:{documentFile:async()=>new Blob(['fake-pdf-bytes'])},pdfModule:{loadPdf:data=>{bytes=data;return {promise:Promise.resolve(pdf),destroy:async()=>{}}}},window:{devicePixelRatio:1}}
 const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText
 const vm=new Function(...Object.keys(env),output)(...Object.values(env));vm.canvas.value={style:{}};vm.container.value={clientWidth:500}
 await vm.load();assert.ok(bytes instanceof ArrayBuffer);assert.deepEqual(requested,[1]);assert.equal(rendered[0].n,1)
 props.page=2;await nextTick();await new Promise(r=>setImmediate(r));assert.deepEqual(requested,[1,2]);assert.equal(rendered[1].n,2);assert.equal(vm.busy.value,false);assert.equal(vm.error.value,'');disposed.forEach(fn=>fn())
})
test('compatibility Hangul composes across original graphemes with exact source mapping',()=>{
 for(const [text,quote,expected] of [['앞 ㄱㅏ 뒤','가','ㄱㅏ'],['😀 ㄱㅏ Cafe\u0301 뒤','가 Café','ㄱㅏ Cafe\u0301'],['x か\u3099 y','が','か\u3099']]){
  const chunks=docs.highlightQuote(text,quote)
  assert.equal(chunks.find(c=>c.highlight)?.text,expected)
  assert.equal(chunks.map(c=>c.text).join(''),text)
 }
})
