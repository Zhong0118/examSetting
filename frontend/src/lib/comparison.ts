import type { api, Job, JobInput, Evaluation } from './api'
type Service=Pick<typeof api,'startJob'|'job'|'createEvaluation'>
export interface ComparisonState {
  operationId: string
  revision: number
  owner?: string
  requestIds: Partial<Record<'baseline'|'grounded',string>>
  input: JobInput
  phase: 'baseline' | 'grounded' | 'report' | 'done' | 'ended'
  paused: boolean
  error?: string
  permanentError?: boolean
  baseline?: Job
  grounded?: Job
  evaluation?: Evaluation
}
export function createComparison(service:Service,storage:Pick<Storage,'getItem'|'setItem'>,key:string,changed:(state:ComparisonState|null)=>void,beforeStart:(state:ComparisonState)=>Promise<void>=async()=>{}) {
  let state:ComparisonState|null=null,busy=false,disposed=false,stored:string|null=null
  const owner=crypto.randomUUID()
  function publish(){changed(state?JSON.parse(JSON.stringify(state)):null)}
  function current(){return storage.getItem(key)===stored}
  function persist(){
    if(!current())throw new Error('对比已在其他页面继续，请重新读取本地进度')
    if(state){state.revision++;stored=JSON.stringify(state);storage.setItem(key,stored)}
    publish()
  }
  function restore(){
    stored=storage.getItem(key);if(!stored)return null
    const saved=JSON.parse(stored)
    if(!saved?.input?.documentId||!['baseline','grounded','report','done','ended'].includes(saved.phase))throw new Error('无法识别保存的对比任务，请检查本地记录')
    state={...saved,operationId:saved.operationId||crypto.randomUUID(),revision:saved.revision||0,requestIds:saved.requestIds||{},paused:!['done','ended'].includes(saved.phase)}
    publish();return state
  }
  async function tick(){
    if(!state||state.paused||['done','ended'].includes(state.phase)||busy||disposed)return
    busy=true
    try{
      while(state&&!state.paused&&!disposed){
        if(!current())throw new Error('对比已在其他页面继续，请重新读取本地进度')
        if(state.phase==='report'){
          const result=await service.createEvaluation([state.baseline!.id,state.grounded!.id])
          if(disposed||!current())return
          state.evaluation=result.evaluation;state.phase='done';persist();return
        }
        if(state.phase==='done'||state.phase==='ended')return
        const strategy=state.phase,previous=state[strategy]
        if(!previous&&!state.requestIds[strategy]){
          await beforeStart(state)
          if(disposed||!current()||state.paused)return
          state.requestIds[strategy]=`${state.operationId}-${strategy}`;persist()
        }
        const result=previous?await service.job(previous.id):await service.startJob({...state.input,strategy,requestId:state.requestIds[strategy]})
        // Late GETs are disposable. A late POST may fill its ID only while this
        // exact stored revision still belongs to us; retries reuse its saved token.
        if(!current()||(disposed&&previous))return
        state[strategy]=result.job;persist()
        if(disposed||state.paused)return
        if(result.job.status==='queued'||result.job.status==='running'||result.job.metadata?.metricsFinalized===false)return
        state.phase=strategy==='baseline'?'grounded':'report';persist()
      }
    }catch(error){
      if(state&&!disposed){state.paused=true;state.error=error instanceof Error?error.message:String(error);state.permanentError=[400,404,410,422].includes(Number((error as {status?:number}).status));if(current())persist();else publish()}
      throw error
    }finally{busy=false}
  }
  async function start(input:JobInput){
    if(busy||disposed)throw new Error('对比任务仍在处理中')
    restore()
    if(state&&!['done','ended'].includes(state.phase))throw new Error('请先继续或结束当前对比，避免丢失已启动任务')
    state={operationId:crypto.randomUUID(),revision:0,owner,requestIds:{},input:JSON.parse(JSON.stringify(input)),phase:'baseline',paused:false};persist();await tick()
  }
  async function resume(){if(busy||disposed)return;restore();if(!state||['done','ended'].includes(state.phase))return;state.owner=owner;state.paused=false;state.error=undefined;state.permanentError=false;persist();await tick()}
  function pause(){if(state&&!disposed&&current()){state.paused=true;persist()}}
  function end(){
    if(busy||disposed)throw new Error('请等待当前请求结束后再结束对比')
    if(!state||!current())throw new Error('对比进度已变化，请重新读取后再结束')
    state.phase='ended';state.paused=false
    storage.setItem(`${key}:archive:${state.operationId}`,JSON.stringify(state));persist()
  }
  function dispose(){disposed=true}
  return {restore,start,resume,pause,end,tick,dispose}
}
