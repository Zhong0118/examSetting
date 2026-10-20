import type { TutorCreate, TutorCommand, TutorSession } from './tutor'
export type TutorOperation = {kind:'create';body:TutorCreate}|{kind:'command';sessionId:string;body:TutorCommand}
type NewOperation = {kind:'create';body:Omit<TutorCreate,'requestId'>}|{kind:'command';sessionId:string;body:Omit<TutorCommand,'requestId'>}
export interface PendingTutorRequest { operation:TutorOperation; blocked?:boolean; error?:string }
type Store=Pick<Storage,'getItem'|'setItem'|'removeItem'>
// The persisted envelope is the exact replay payload, not a form that can change underneath a POST.
export function createTutorRequest(store:Store,key:string,send:(operation:TutorOperation)=>Promise<TutorSession>,changed:(pending:PendingTutorRequest|null)=>void,received:(session:TutorSession)=>void,active=()=>true){
  let disposed=false,busy=false
  function restore(){const raw=store.getItem(key);const pending:PendingTutorRequest|null=raw?JSON.parse(raw):null;changed(pending);return pending}
  async function retry(){
    if(disposed||busy||!active())return
    const pending=restore();if(!pending)return
    if(pending.blocked)throw new Error('此请求已被拒绝，请先读取最新状态并保留旧记录后重新操作')
    const snapshot=store.getItem(key);busy=true
    const current=()=>!disposed&&active()&&store.getItem(key)===snapshot
    try{const session=await send(pending.operation);if(!current())return;store.removeItem(key);changed(null);received(session)}
    catch(error){
      if(current()&&(error as {code?:string}).code!=='session_changed'){
        pending.error=error instanceof Error?error.message:String(error)
        pending.blocked=[400,403,404,409,410,422].includes(Number((error as {status?:number}).status))
        store.setItem(key,JSON.stringify(pending));changed(pending)
      }
      throw error
    }finally{busy=false}
  }
  async function submit(operation:NewOperation){
    if(disposed||busy||!active())return
    if(store.getItem(key)){restore();throw new Error('已有待确认请求，请先恢复它，避免重复提交')}
    const pending={operation:{...operation,body:{...operation.body,requestId:crypto.randomUUID()}}} as PendingTutorRequest
    store.setItem(key,JSON.stringify(pending));changed(pending);await retry()
  }
  function discard(){
    if(disposed||busy||!active())return
    const pending=restore();if(!pending)return
    if(!pending.blocked)throw new Error('尚不确定服务是否已接受请求，请使用原请求重试')
    store.setItem(`${key}:archive:${pending.operation.body.requestId}`,JSON.stringify(pending))
    store.removeItem(key);changed(null)
  }
  return {restore,retry,submit,discard,dispose:()=>{disposed=true}}
}
export function createTutorReader(read:()=>Promise<TutorSession>,received:(session:TutorSession)=>void,active=()=>true){
  let generation=0,disposed=false,version=-1
  return {
    async read(){if(disposed||!active())return;const token=++generation;try{const session=await read();if(disposed||!active()||token!==generation||session.version<version)return;version=session.version;received(session)}catch(e){if(!disposed&&active()&&token===generation)throw e}},
    dispose(){disposed=true;generation++},
  }
}
