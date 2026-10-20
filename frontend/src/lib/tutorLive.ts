import { request } from './api'
import type { JSONValue } from './tutor'

export interface LiveDataset { id:string; version:string; hash:string; cases:{id:string;title:string;goal:string}[]; limitations:string[] }
export interface LiveStart { requestId:string; caseIds:string[]; repeats:number; maxCalls:number }
export type LiveDimension = 'accuracy'|'grounding'|'diagnosis'|'actionability'
export interface LiveReviewInput { version:number; reviewer:string; reviewerType:'human'|'ai-assisted'; scores:Record<LiveDimension,number>; notes:string }
export type LiveReview = Omit<LiveReviewInput,'version'> & {updatedAt:string}
export interface LiveTrial {
  id:string; blindId:string; caseId:string; title:string; strategy:'rule'|'agent'; repeat:number
  status:'pending'|'running'|'completed'|'failed'|'budget'|'cancelled'|'interrupted'; error:string|null
  modelCalls:number; elapsedMs:number|null; usage:null|{prompt_tokens:number;completion_tokens:number;total_tokens:number}
  steps:JSONValue[]; session:JSONValue; checks:{code:string;message:string;passed:boolean}[]; review:LiveReview|null
}
export interface LiveSummary { trials:number; completed:number; passed:number; checks:number; passedChecks:number; modelCalls:number }
export interface LiveReport {
  kind:'live-tutor-evaluation'; datasetId:string; datasetVersion:string; datasetHash:string; promptHash:string
  graderVersion?:string
  parameters:JSONValue; learner:'fixed-script'; trials:LiveTrial[]; summary:Record<'rule'|'agent',LiveSummary>; limitations:string[]; rubric:JSONValue
}
export interface LiveEvaluation {
  id:string; version:number; status:'queued'|'running'|'completed'|'cancelled'|'interrupted'|'failed'; createdAt:string; updatedAt:string
  model:string; provider:string; datasetHash:string; promptHash:string; maxCalls:number; modelCalls:number; error:string|null; report:LiveReport; busy?:boolean
}
export interface LiveBlindPackage {
  kind:string; version:string|number; datasetHash:string; rubric:JSONValue; limitations?:string[]
  items:{blindId:string;caseTitle:string;goal:string;questions:JSONValue[];answers:JSONValue[];events:JSONValue[]}[]
}
const path='/tutor/live-evaluations'
export const tutorLiveApi = {
  dataset:()=>request<{dataset:LiveDataset}>(`${path}/dataset`),
  create:(body:LiveStart)=>request<{evaluation:LiveEvaluation}>(path,'POST',body),
  evaluations:()=>request<{evaluations:LiveEvaluation[]}>(path),
  evaluation:(id:string)=>request<{evaluation:LiveEvaluation}>(`${path}/${encodeURIComponent(id)}`),
  cancel:(id:string)=>request<{evaluation:LiveEvaluation}>(`${path}/${encodeURIComponent(id)}/cancel`,'POST'),
  blind:(id:string)=>request<{package:LiveBlindPackage}>(`${path}/${encodeURIComponent(id)}/blind`),
  review:(id:string,blindId:string,body:LiveReviewInput)=>request<{evaluation:LiveEvaluation}>(`${path}/${encodeURIComponent(id)}/reviews/${encodeURIComponent(blindId)}`,'PUT',body),
}
export const liveStatus={queued:'等待运行',running:'正在运行',completed:'已完成',cancelled:'已取消',interrupted:'已中断',failed:'失败',pending:'未运行',budget:'预算耗尽'}
export const liveDimensions:{key:LiveDimension;label:string}[]=[{key:'accuracy',label:'事实正确'},{key:'grounding',label:'证据支持'},{key:'diagnosis',label:'误区诊断'},{key:'actionability',label:'下一步可执行'}]
export function liveStartValid(body:Omit<LiveStart,'requestId'>){
  return body.caseIds.length>=1&&body.caseIds.length<=4&&new Set(body.caseIds).size===body.caseIds.length&&body.caseIds.every(id=>typeof id==='string'&&!!id.trim())&&Number.isInteger(body.repeats)&&body.repeats>=1&&body.repeats<=3&&Number.isInteger(body.maxCalls)&&body.maxCalls>=1&&body.maxCalls<=20
}
export interface PendingLiveStart {body:LiveStart;blocked?:boolean;error?:string}
type Store=Pick<Storage,'getItem'|'setItem'|'removeItem'>
// Local persistence precedes POST. Restore is read-only; only explicit retry can replay the exact body.
export function createLiveStartRequest(store:Store,key:string,send:(body:LiveStart)=>Promise<LiveEvaluation>,changed:(pending:PendingLiveStart|null)=>void,received:(evaluation:LiveEvaluation)=>void,active=()=>true){
  let disposed=false,busy=false
  function restore(){
    const raw=store.getItem(key),pending:PendingLiveStart|null=raw?JSON.parse(raw):null
    if(pending&&(!pending.body||typeof pending.body.requestId!=='string'||!pending.body.requestId||!Array.isArray(pending.body.caseIds)||!liveStartValid(pending.body)))throw new Error('待确认请求记录无法读取，请保留浏览器记录后核对历史作业')
    if(!disposed&&active())changed(pending)
    return pending
  }
  async function retry(){
    if(disposed||busy||!active())return
    const pending=restore();if(!pending)return
    if(pending.blocked)throw new Error('此请求已被拒绝，请保留记录后重新填写')
    const snapshot=store.getItem(key);busy=true
    const current=()=>!disposed&&active()&&store.getItem(key)===snapshot
    try{const evaluation=await send(pending.body);if(!current())return;store.removeItem(key);changed(null);received(evaluation)}
    catch(error){
      if(current()&&(error as {code?:string}).code!=='session_changed'){
        pending.error=error instanceof Error?error.message:String(error)
        pending.blocked=[400,401,403,404,409,410,422].includes(Number((error as {status?:number}).status))
        store.setItem(key,JSON.stringify(pending));changed(pending)
      }
      throw error
    }finally{busy=false}
  }
  async function submit(body:Omit<LiveStart,'requestId'>){
    if(disposed||busy||!active())return
    if(store.getItem(key)){restore();throw new Error('已有待确认请求，请先使用原请求重试')}
    if(!liveStartValid(body))throw new Error('请选择 1–4 个场景、1–3 次重复和 1–20 次调用预算')
    const pending={body:{...body,caseIds:[...body.caseIds],requestId:crypto.randomUUID()}}
    store.setItem(key,JSON.stringify(pending));changed(pending);await retry()
  }
  function discard(){
    if(disposed||busy||!active())return
    const pending=restore();if(!pending)return
    if(!pending.blocked)throw new Error('结果尚未确认，请使用原请求重试，避免重复付费')
    store.setItem(`${key}:archive:${pending.body.requestId}`,JSON.stringify(pending));store.removeItem(key);changed(null)
  }
  return {restore,retry,submit,discard,dispose:()=>{disposed=true}}
}
