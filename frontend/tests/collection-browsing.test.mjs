import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { script, deferred, storage } from './harness.mjs'

// Bind one Vue runtime explicitly: the harness defaults and compiler must share reactivity.
const require=createRequire(new URL('../package.json',import.meta.url)), Vue=require('vue')
const {ref,reactive,nextTick,effectScope,computed,watch,proxyRefs}=Vue
const {renderToString}=require('vue/server-renderer')
const component='views/CollectionView.vue'
const names=['home','library','sets','attempts','loading','error','q','topic','scope','topics','total','page','pageSize','filtered','featured','resumed','load','changePage']
const fixtures=Array.from({length:26},(_,i)=>({id:`S${i+1}`,title:i===25?'远处的微积分':`题集 ${i+1}`,description:'练习说明',topic:i===25?'微积分':'代数',visibility:'private',version:1,questionCount:3,author:'访客',ownerId:'U',isOwner:true,bookmarked:false,updatedAt:'2026-10-20',sourceSetId:null}))
const result=(sets=fixtures.slice(0,12),options={})=>({sets,total:26,page:1,pageSize:12,topics:['代数','微积分'],...options})
const settle=async()=>{for(let i=0;i<6;i++)await nextTick()}

async function collection(path='/library',overrides={}){
  const calls=[],timers=new Map(),lifecycle=[],local=storage(),scope=effectScope()
  let mounted=()=>{},timerId=0,historyReads=0
  const bindings={ref,computed,watch,nextTick,useRoute:()=>({path}),user:ref({id:'U',email:null}),authOpen:ref(false),localStorage:local,
    draftKey:(user,id,version)=>`${user}:${id}:${version}`,date:x=>x,scoreLabel:()=>'',message:e=>e.message,
    setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId},clearTimeout:id=>timers.delete(id),
    onMounted:fn=>mounted=fn,onBeforeUnmount:fn=>lifecycle.push(fn),
    api:{sets:async()=>overrides.setsPage?overrides.setsPage('legacy',{page:1}):result(),setsPage:async(scope,options)=>{
      calls.push({scope,...options})
      if(overrides.setsPage)return overrides.setsPage(scope,options)
      const matches=fixtures.filter(s=>(!options.q||s.title.includes(options.q))&&(!options.topic||s.topic===options.topic))
      const page=Math.min(options.page,Math.max(1,Math.ceil(matches.length/12)))
      return result(matches.slice((page-1)*12,page*12),{total:matches.length,page})
    },attempts:async()=>{historyReads++;return {attempts:overrides.attempts||[]}}}}
  // script() reads asynchronously, so bind watch to the scope for cleanup.
  bindings.watch=(...args)=>scope.run(()=>watch(...args))
  const vm=await script(component,bindings,names)
  const dispose=()=>{lifecycle.forEach(fn=>fn());scope.stop()}
  const advance=()=>{const pending=[...timers.values()];timers.clear();pending.forEach(({fn})=>fn())}
  return {vm,bindings,calls,timers,local,mount:()=>mounted(),dispose,advance,historyReads:()=>historyReads}
}

async function compiled(path){
  const source=await readFile(new URL(`../src/${path}`,import.meta.url),'utf8')
  return Vue.compile(source.match(/<template>([\s\S]*)<\/template>/)[1])
}
async function collectionHTML(vm,bindings){
  const render=await compiled(component),listRender=await compiled('components/SetList.vue')
  const app=Vue.createSSRApp({setup:()=>({...bindings,...vm}),render})
  app.component('RouterLink',{setup:(_,ctx)=>()=>Vue.h('a',null,ctx.slots.default?.())})
  app.component('Icon',{render:()=>Vue.h('svg')})
  app.component('Pagination',{render:()=>null})
  app.component('SetList',{props:['sets'],setup:props=>()=>listRender({...props,date:x=>x,visibilityLabels:{private:'仅自己'}},[])})
  return renderToString(app)
}

for(const [path,scope] of [['/','workspace'],['/library','mine'],['/discover','discover']]){
  test(`${path} requests 12 server results and uses facets outside the current page`,async t=>{
    const e=await collection(path);t.after(e.dispose);await e.vm.load()
    assert.deepEqual(e.calls,[{scope,page:1,pageSize:12,q:'',topic:''}])
    assert.equal(e.vm.sets.value.length,12);assert.equal(e.vm.total.value,26)
    assert.deepEqual(e.vm.topics.value,['代数','微积分'])
  })
}

test('search on page two resets to page one, debounces typing and finds a set outside loaded pages',async t=>{
  const e=await collection();t.after(e.dispose);await e.vm.load();e.vm.changePage(2);await settle()
  assert.equal(e.vm.sets.value[0].id,'S13')
  e.vm.q.value='远';e.vm.q.value='远处';await settle()
  assert.equal(e.vm.page.value,1);assert.equal(e.vm.loading.value,true)
  assert.equal(e.vm.sets.value.length,0);assert.equal(e.vm.total.value,0)
  assert.equal(e.calls.length,2);assert.equal(e.timers.size,1)
  assert.equal([...e.timers.values()][0].ms,250)
  e.advance();await settle()
  assert.deepEqual(e.calls.at(-1),{scope:'mine',page:1,pageSize:12,q:'远处',topic:''})
  assert.deepEqual(e.vm.sets.value.map(s=>s.id),['S26']);assert.equal(e.vm.total.value,1)
})

test('topic and library scope changes reset pagination and saved scope clears the previous topic',async t=>{
  const e=await collection();t.after(e.dispose);await e.vm.load();e.vm.changePage(3);await settle()
  e.vm.topic.value='微积分';await settle()
  assert.deepEqual(e.calls.at(-1),{scope:'mine',page:1,pageSize:12,q:'',topic:'微积分'})
  assert.deepEqual(e.vm.sets.value.map(s=>s.id),['S26'])
  e.vm.scope.value='saved';await settle()
  assert.deepEqual(e.calls.at(-1),{scope:'saved',page:1,pageSize:12,q:'',topic:''})
  assert.equal(e.vm.topic.value,'');assert.equal(e.vm.sets.value.length,12)
})

test('typing and clearing in the same turn still schedules the current unfiltered request',async t=>{
  const e=await collection();t.after(e.dispose);await e.vm.load()
  e.vm.q.value='远处';e.vm.q.value='';await settle()
  assert.equal(e.timers.size,1)
  e.advance();await settle()
  assert.equal(e.calls.length,2);assert.equal(e.calls.at(-1).q,'')
  assert.equal(e.vm.loading.value,false);assert.equal(e.vm.total.value,26)
})

for(const failed of [false,true]){
  test(`an old ${failed?'failure':'success'} during the debounce cannot publish data or end loading`,async t=>{
    const pending=deferred(),e=await collection('/discover',{setsPage:()=>pending.promise});t.after(e.dispose)
    const old=e.vm.load();e.vm.q.value='远处'
    // Resolve in the same turn: invalidation must happen when typing starts, not after 250ms.
    if(failed)pending.reject(new Error('旧请求失败'));else pending.resolve(result())
    await old;await settle()
    assert.equal(e.vm.sets.value.length,0);assert.equal(e.vm.total.value,0)
    assert.equal(e.vm.error.value,'');assert.equal(e.vm.loading.value,true)
    assert.equal(e.calls.length,1);assert.equal(e.timers.size,1)
  })
}

test('a late previous page cannot overwrite newer sets, totals, facets or the server-clamped page',async t=>{
  const old=deferred(),e=await collection('/library',{setsPage:(_,options)=>options.page===2?old.promise:Promise.resolve(options.topic?result([fixtures[25]],{total:1,topics:['微积分']}):result())});t.after(e.dispose)
  await e.vm.load();e.vm.changePage(2);e.vm.topic.value='微积分';await settle()
  old.resolve(result(fixtures.slice(12,24),{page:2,topics:['旧主题']}));await settle()
  assert.deepEqual(e.vm.sets.value.map(s=>s.id),['S26']);assert.equal(e.vm.total.value,1)
  assert.equal(e.vm.page.value,1);assert.deepEqual(e.vm.topics.value,['微积分'])
  assert.equal(e.vm.error.value,'');assert.equal(e.vm.loading.value,false)
})

test('pagination adopts a clamped server page without issuing another request',async t=>{
  let reduced=false
  const e=await collection('/discover',{setsPage:()=>Promise.resolve(reduced?result([fixtures[0]],{total:1,page:1}):result())});t.after(e.dispose)
  await e.vm.load();reduced=true;e.vm.changePage(3);await settle()
  assert.equal(e.calls.at(-1).page,3);assert.equal(e.vm.page.value,1)
  assert.equal(e.vm.sets.value[0].id,'S1');assert.equal(e.calls.length,2)
})

test('loading and failure never render previous-filter results and retry uses the current query',async t=>{
  let fail=false
  const e=await collection('/discover',{setsPage:async()=>{if(fail)throw new Error('离线');return result()}});t.after(e.dispose)
  await e.vm.load();assert.match(await collectionHTML(e.vm,e.bindings),/题集 1/)
  fail=true;e.vm.q.value='远处'
  assert.doesNotMatch(await collectionHTML(e.vm,e.bindings),/题集 1/)
  e.advance();await settle();assert.equal(e.vm.error.value,'离线')
  assert.doesNotMatch(await collectionHTML(e.vm,e.bindings),/题集 1/)
  fail=false;await e.vm.load()
  assert.equal(e.calls.at(-1).q,'远处');assert.equal(e.vm.error.value,'');assert.equal(e.vm.loading.value,false)
})

test('unmount clears debounce and late collection or history responses cannot update state',async()=>{
  const pending=deferred(),history=deferred(),e=await collection('/',{setsPage:()=>pending.promise})
  e.bindings.api.attempts=()=>history.promise
  e.mount();e.vm.q.value='远处';await settle();assert.equal(e.timers.size,1)
  e.dispose();const before={sets:e.vm.sets.value,attempts:e.vm.attempts.value,loading:e.vm.loading.value,error:e.vm.error.value}
  pending.resolve(result());history.resolve({attempts:[{id:'late',setId:'S1'}]});e.advance();await settle()
  assert.equal(e.timers.size,0);assert.equal(e.calls.length,1)
  assert.deepEqual({sets:e.vm.sets.value,attempts:e.vm.attempts.value,loading:e.vm.loading.value,error:e.vm.error.value},before)
})

for(const hasDraft of [false,true]){
  test(`home keeps its initial ${hasDraft?'unfinished draft':'recent practice'} recommendation across pages and filters`,async t=>{
    const e=await collection('/',{attempts:[{id:'A',setId:'S2',setTitle:'题集 2'}]});t.after(e.dispose)
    if(hasDraft)e.local.setItem('U:S3:1',JSON.stringify({q:'未完成的回答'}))
    e.mount();await settle();assert.equal(e.vm.featured.value.id,hasDraft?'S3':'S2')
    e.vm.changePage(2);await settle();e.vm.topic.value='微积分';await settle()
    assert.deepEqual(e.vm.sets.value.map(s=>s.id),['S26'])
    assert.equal(e.vm.featured.value.id,hasDraft?'S3':'S2');assert.equal(!!e.vm.resumed.value,hasDraft)
    assert.equal(e.vm.attempts.value[0].id,'A');assert.equal(e.historyReads(),1)
    const html=await collectionHTML(e.vm,e.bindings)
    assert.match(html,/当前为访客空间/);assert.match(html,/绑定账户保留学习记录/)
    const chips=html.match(/<div class="topic-collections">([\s\S]*?)<\/div>/)[1]
    assert.match(chips,/微积分/);assert.doesNotMatch(chips,/\d+\s*份/)
  })
}

test('pagination renders native bounded controls, totals, optional aria label and hides a single page',async()=>{
  const props=reactive({page:1,total:26,pageSize:12,label:'题目分页'}),events=[]
  const vm=await script('components/Pagination.vue',{ref,computed,watch,defineProps:()=>props,defineEmits:()=> (...args)=>events.push(args)},['props','pages','emit'])
  const render=await compiled('components/Pagination.vue'),ctx=proxyRefs(vm)
  const nav=async()=>{
    let node
    const app=Vue.createSSRApp({render:()=>{const tree=render(ctx,[]);node=tree.children.default()[0];return tree}})
    app.component('Icon',{render:()=>Vue.h('svg')})
    await renderToString(app)
    return node
  }
  let node=await nav();assert.equal(node.type,'nav');assert.equal(node.props['aria-label'],'题目分页')
  let buttons=node.children.filter(child=>child.type==='button')
  assert.equal(buttons.length,2);assert.equal(buttons[0].props.type,'button');assert.equal(buttons[1].props.type,'button')
  assert.equal(buttons[0].props.disabled,true);assert.equal(buttons[1].props.disabled,false)
  buttons[1].props.onClick();assert.deepEqual(events,[['change',2]])
  const text=()=>node.children.filter(child=>child.type==='span').map(child=>child.children).join(' ')
  assert.match(text(),/共 26 项/);assert.match(text(),/第 1\/3 页/)
  props.page=3;node=await nav();buttons=node.children.filter(child=>child.type==='button')
  assert.equal(buttons[0].props.disabled,false);assert.equal(buttons[1].props.disabled,true)
  buttons[0].props.onClick();assert.deepEqual(events,[['change',2],['change',2]])
  props.label=undefined;assert.equal((await nav()).props['aria-label'],'题集分页')
  props.total=12;assert.notEqual((await nav()).type,'nav');props.total=0;assert.notEqual((await nav()).type,'nav')
})
