import { readFile } from 'node:fs/promises'
import ts from 'typescript'
import { ref, shallowRef, computed, watch, nextTick } from 'vue'
export async function script(path, bindings, names) {
  let source = await readFile(new URL(`../src/${path}`, import.meta.url), 'utf8')
  source = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)?.[1] || source
  source = source.replace(/^import .*$/gm, '').replace(/^export /gm, '')
  source += `\nreturn {${names.map(n => `${n}:typeof ${n} === 'undefined' ? undefined : ${n}`).join(',')}}`
  const defaults = {ref,shallowRef,computed,watch,nextTick,onMounted:()=>{},onBeforeUnmount:()=>{},onBeforeRouteLeave:()=>{}}
  const env = {...defaults,...bindings}
  const {outputText} = ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}})
  return new Function(...Object.keys(env),outputText)(...Object.values(env))
}
export function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject}}
export function storage(){const map=new Map();return {get length(){return map.size},key:i=>[...map.keys()][i]??null,getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k),map}}

export async function renderView(path, bindings, names, prepare=()=>{}) {
  const Vue=await import('vue'), server=await import('vue/server-renderer')
  const {parse,compileTemplate}=await import('vue/compiler-sfc')
  const source=await readFile(new URL(`../src/${path}`,import.meta.url),'utf8')
  const {code,errors}=compileTemplate({source:parse(source).descriptor.template.content,filename:path,id:'regression',ssr:true,ssrCssVars:[]})
  if(errors.length)throw errors[0]
  const executable=code.replace(/import \{([^}]+)\} from "([^"]+)"/g,(_,names,module)=>`const {${names.replace(/\bas\b/g,':')}} = ${module==='vue'?'Vue':'server'}`).replace('export function','function')
  const ssrRender=new Function('Vue','server',`${ts.transpileModule(executable,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText};return ssrRender`)(Vue,server)
  const vm=await script(path,bindings,names);prepare(vm)
  const component={setup:()=>({...bindings,...vm}),ssrRender}
  const app=Vue.createSSRApp(component)
  app.component('RouterLink',{setup:(_,ctx)=>()=>Vue.h('a',null,ctx.slots.default?.())})
  app.component('Icon',{render:()=>Vue.h('svg')})
  for(const name of ['AttemptResult','SetList','CitationCard','QualityPanel','DocumentRange','ComparisonReport','TutorBenchmark','TutorLiveEvaluation','TutorTranscript'])app.component(name,{render:()=>null})
  return server.renderToString(app)
}
