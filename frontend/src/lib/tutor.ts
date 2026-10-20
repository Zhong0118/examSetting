import { request, type PracticeQuestion, type Citation } from './api'
export type TutorMode = 'rule' | 'agent'
export interface TutorCreate { requestId: string; setId: string; goal: string; mode: TutorMode; maxQuestions: number }
export interface TutorCommand { requestId: string; version: number; type: 'answer' | 'resume' | 'stop'; answer?: string; turnId?: number }
export interface TutorAnswer {
  kind:'question'|'followup'; questionId:string; turnId:number; prompt:string; userAnswer:string; correct:boolean|null
  type?:'single'|'short'; options?:string[]; answer?:string; explanation?:string; source?:string; topic?:string; citation?:Citation|null
}
export interface TutorEvidence {evidenceId:string;questionId:string;quote:string;citation:Citation|null}
export interface TutorEvent {id:string;type:'question'|'followup'|'answer'|'feedback'|'finish';message:string;questionId?:string;turnId?:number;result?:TutorAnswer;evidence?:TutorEvidence[];summary?:TutorSession['summary']}
export interface TutorTrace {tool:string;status:'ok'|'error';message:string;argsSummary?:string;resultSummary?:string;elapsedMs?:number}
export interface TutorSession {
  id: string; setId: string; setTitle: string; setVersion: number; version: number; createdAt: string; updatedAt: string
  goal: string; mode: TutorMode; maxQuestions: number; status: 'running' | 'waiting' | 'paused' | 'completed'; busy: boolean
  turnId: number; pending: {kind:'question'|'followup';questionId:string;prompt:string}|null; currentQuestion: PracticeQuestion|null
  asked: string[]; answers: TutorAnswer[]; events: TutorEvent[]; trace: TutorTrace[]
  summary: {answered:number;correct:number;objectiveTotal:number;followups:number}
  budget: {maxModelCalls:number;maxModelCallsPerTurn:number;maxRuleStepsPerTurn:number;remainingModelCalls:number}
  timingIncomplete?:boolean; model?:string|null; provider?:string; policyVersion?:string
  modelCalls: number; elapsedMs: number|null; error?: string|null; stopReason?: string|null
}
export type TutorSummary = Omit<TutorSession,'events'|'trace'|'answers'|'currentQuestion'|'pending'>
export const tutorApi = {
  sessions: () => request<{sessions:TutorSummary[]}>('/tutor/sessions'),
  create: (data:TutorCreate) => request<{session:TutorSession}>('/tutor/sessions','POST',data),
  session: (id:string) => request<{session:TutorSession}>(`/tutor/sessions/${encodeURIComponent(id)}`),
  command: (id:string,data:TutorCommand) => request<{session:TutorSession}>(`/tutor/sessions/${encodeURIComponent(id)}/commands`,'POST',data),
  benchmark: () => request<{report:TutorBenchmarkReport}>('/tutor/benchmark','POST'),
}
export const tutorStatus = {running:'教练正在处理',waiting:'等待你的回答',paused:'已暂停',completed:'本次学习已结束'}
export const tutorMode = {rule:'规则教练',agent:'Agent 教练'}

export function tutorToolLabel(tool:string){return ({read_history:'查阅学习记录',search_materials:'检索题目附带资料',ask_question:'选择下一题',ask_followup:'追问作答理由',give_feedback:'给出学习反馈',finish:'结束并总结',runtime:'运行检查'} as Record<string,string>)[tool]||'工具检查'}

export type JSONValue=null|boolean|number|string|JSONValue[]|{[key:string]:JSONValue}
export interface TutorBenchmarkCheck {code:string;message:string;expected:JSONValue;observed:JSONValue;passed:boolean}
export interface TutorBenchmarkTrace {step:number;operation:'rule'|'action'|'answer'|'probe'|'answer-probe';tool:string|null;input:JSONValue;outcome:'applied'|'rejected'|'error';error:string|null;stateUnchanged:boolean;status:string;turnId:number;engineTrace:TutorTrace[]}
export interface TutorBenchmarkCase {id:string;title:string;category:'teaching'|'safety';goal:string;expected:{code:string;field:string;equals:JSONValue;message:string}[];observed:Record<string,JSONValue>;checks:TutorBenchmarkCheck[];actualTrace:TutorBenchmarkTrace[];passed:boolean;error:string|null}
export interface TutorBenchmarkStrategy {name:'rule'|'scripted-agent';label:string;summary:{checks:number;passedChecks:number;passRate:number;cases:number;passedCases:number;errorCases:number};cases:TutorBenchmarkCase[]}
export interface TutorBenchmarkReport {kind:'tutor-behavior-benchmark';version:string;datasetId:string;datasetVersion:string;datasetHash:string;createdAt:string;caseCount:number;strategies:TutorBenchmarkStrategy[];limitations:string[]}
export function benchmarkValue(value:JSONValue):string {if(value===null)return '无';if(typeof value==='boolean')return value?'是':'否';if(typeof value==='string')return ({running:'运行中',waiting:'等待作答',paused:'已暂停',completed:'已完成',question:'题目',followup:'追问'} as Record<string,string>)[value]||value;return JSON.stringify(value)}
