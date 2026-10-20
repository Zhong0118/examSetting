export interface User { id: string; name: string; email: string | null }
export type Visibility = 'private' | 'unlisted' | 'public'
export interface Question { id: string; type: 'single' | 'short'; prompt: string; options: string[]; answer?: string; explanation?: string; source: string; topic: string; citation?: Citation | null }
export type PracticeQuestion = Omit<Question, 'answer' | 'explanation' | 'source' | 'citation'>
export interface SetSummary { id: string; title: string; description: string; topic: string; visibility: Visibility; version: number; questionCount: number; author: string; ownerId: string; isOwner: boolean; bookmarked: boolean; updatedAt: string; sourceSetId: string | null }
export interface SetPage { sets: SetSummary[]; total: number; page: number; pageSize: number; topics: string[] }
export interface SetDetail extends SetSummary { questions: Question[] }
export interface SetInput { title: string; description: string; topic: string; visibility: Visibility; questions: Question[]; version?: number }
export interface Result extends Question { userAnswer: string; correct: boolean | null; questionId: string }
export interface Attempt { id: string; setId: string; setTitle: string; version: number; createdAt: string; correct: number; total: number; results: Result[] }
export interface AIConfig { configured: boolean; baseUrl: string; model: string }
export interface Job { id: string; status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'; error: string | null; questions: Question[]; createdAt: string; metadata?: JobMetadata; quality?: QualityReport | null }
export class ApiError extends Error { constructor(message: string, public status: number, public code?: string) { super(message) } }
let expectedUser: string | null = null
let sessionBlocked = false
let identityGeneration = 0
let identityChanged: () => void = () => {}
export function setExpectedUser(value: string | null) { expectedUser = value; sessionBlocked = false; identityGeneration++ }
export function setSessionBlocked(value: boolean) { sessionBlocked = value; if(value) identityGeneration++ }
export function onSessionChanged(handler: () => void) { identityChanged = handler }
function identityError() { return new ApiError('账户已在其他页面切换；请确认当前账户后继续，原账户草稿已保留', 409, 'session_changed') }

export async function request<T>(path: string, method = 'GET', body?: unknown, format: 'json' | 'blob' = 'json'): Promise<T> {
  if(sessionBlocked && path !== '/session') throw identityError()
  const generation = identityGeneration
  const multipart = body instanceof FormData
  let response: Response
  try { response = await fetch(`/api${path}`, { method, credentials: 'same-origin', headers: { ...(method !== 'GET' ? { 'X-Requested-With': 'ExamHub', ...(expectedUser ? { 'X-Expected-User': expectedUser } : {}) } : {}), ...(body !== undefined && !multipart ? { 'Content-Type': 'application/json' } : {}) }, ...(body !== undefined ? { body: multipart ? body : JSON.stringify(body) } : {}) }) }
  catch { throw new ApiError('无法连接服务，请检查网络后重试', 0) }
  const data = response.ok && format==='blob' ? await response.blob() : await response.json().catch(() => null)
  if(data?.code === 'session_changed') { setSessionBlocked(true); identityChanged() }
  if (!response.ok) throw new ApiError(data?.error || `请求失败（${response.status}），请稍后重试`, response.status, data?.code)
  if(path !== '/session' && (generation !== identityGeneration || sessionBlocked)) throw identityError()
  if (!data) throw new ApiError('服务返回了无法读取的数据', response.status)
  return data as T
}
const id = encodeURIComponent
export const api = {
  session: () => request<{user: User}>('/session'),
  auth: (mode: 'login' | 'register', data: {name?: string; email: string; password: string}) => request<{user: User}>(`/auth/${mode}`, 'POST', data),
  logout: () => request<{user: User}>('/auth/logout', 'POST'),
  sets: (scope = 'discover', q = '', topic = '') => request<{sets: SetSummary[]}>(`/sets?${new URLSearchParams({scope,q,topic})}`),
  setsPage: (scope = 'discover', options: {q?: string; topic?: string; page?: number; pageSize?: number} = {}) => request<SetPage>(`/sets?${new URLSearchParams({scope, q: options.q ?? '', topic: options.topic ?? '', page: String(options.page ?? 1), pageSize: String(options.pageSize ?? 12)})}`),
  set: (key: string) => request<{set: SetDetail}>(`/sets/${id(key)}`),
  save: (data: SetInput, key?: string) => request<{set: SetDetail}>(key ? `/sets/${id(key)}` : '/sets', key ? 'PUT' : 'POST', data),
  delete: (key: string) => request<{ok: boolean}>(`/sets/${id(key)}`, 'DELETE'),
  bookmark: (key: string) => request<{bookmarked: boolean}>(`/sets/${id(key)}/bookmark`, 'POST'),
  fork: (key: string) => request<{set: SetDetail}>(`/sets/${id(key)}/fork`, 'POST'),
  practice: (key: string) => request<{set: SetSummary; questions: PracticeQuestion[]}>(`/sets/${id(key)}/practice`),
  submit: (key: string, version: number, answers: Record<string,string>) => request<{attempt: Attempt}>(`/sets/${id(key)}/attempts`, 'POST', {version,answers}),
  attempts: () => request<{attempts: Attempt[]}>('/attempts'),
  config: () => request<AIConfig>('/ai/config'),
  saveConfig: (data: {baseUrl: string; model: string; apiKey: string}) => request<AIConfig>('/ai/config', 'PUT', data),
  startJob: (data: JobInput) => request<{job: Job}>('/ai/jobs', 'POST', data),
  job: (key: string) => request<{job: Job}>(`/ai/jobs/${id(key)}`),
  documents: () => request<{documents: StudyDocument[]}>('/documents'),
  uploadDocument: (file: File) => { const body=new FormData();body.append('file',file);return request<{document: StudyDocument; duplicate: boolean}>('/documents','POST',body) },
  document: (key: string) => request<{document: StudyDocument; pages: DocumentPage[]}>(`/documents/${id(key)}`),
  documentFile: (key: string) => request<Blob>(`/documents/${id(key)}/file`,'GET',undefined,'blob'),
  deleteDocument: (key: string) => request<{ok: boolean}>(`/documents/${id(key)}`,'DELETE'),
  checkQuality: (questions: Question[]) => request<{report: QualityReport}>('/quality/check','POST',{questions}),
  setQuality: (key: string) => request<{report: QualityReport; version: number}>(`/sets/${id(key)}/quality`),
  benchmark: () => request<{report: BenchmarkReport}>('/evaluations/benchmark','POST'),
  createEvaluation: (jobIds: [string,string]) => request<{evaluation: Evaluation}>('/evaluations','POST',{jobIds}),
  evaluations: () => request<{evaluations: Evaluation[]}>('/evaluations'),
  evaluation: (key: string) => request<{evaluation: Evaluation}>(`/evaluations/${id(key)}`),
  cancelJob: (key: string) => request<{job: Job}>(`/ai/jobs/${id(key)}`, 'DELETE'),
}

export interface StudyDocument { id: string; title: string; filename: string; sha256: string; pageCount: number; textPageCount: number; createdAt: string; warnings: string[] }
export interface DocumentPage { page: number; text: string; charCount: number }
export interface Citation { documentId: string; documentTitle: string; documentHash: string; page: number; quote: string }
export type Strategy = 'baseline' | 'grounded'
export interface JobInput { requestId?: string; source?: string; title: string; topic: string; count: number; documentId?: string; startPage?: number; endPage?: number; strategy?: Strategy }
export interface JobMetadata { documentTitle?: string; provider?: string; promptVersion?: string; title?: string; topic?: string; strategy: Strategy; documentId: string | null; pages: number[]; sourceHash: string; count: number; model: string; elapsedMs: number | null; timingIncomplete?: boolean; metricsFinalized?: boolean; modelCalls: number }
export interface QualityReport { ruleVersion: string; total: number; passed: number; passRate: number; citationCoverage: number; duplicatePairs: {left: string; right: string; similarity: number}[]; items: {questionId: string; passed: boolean; checks: {code: string; status: 'pass' | 'fail' | 'warn'; message: string}[]}[]; limits: string[] }
export interface BenchmarkReport { kind: 'detector-benchmark'; datasetId: string; datasetHash: string; ruleVersion: string; createdAt: string; sampleCount: number; strategies: {name: string; precision: number; recall: number; tp: number; fp: number; fn: number; tn: number; samples: {id: string; label: boolean | string; predicted: boolean | string; issues: string[]; questions?: Question[]; description?: string}[]}[]; limitations: string[] }
export interface Evaluation { id: string; createdAt: string; kind: 'generation-comparison'; documentTitle: string; sourceHash: string; pages: number[]; count: number; model: string; runs: {jobId: string; strategy: Strategy; status: Job['status']; error: string | null; elapsedMs: number | null; timingIncomplete?: boolean; metricsFinalized?: boolean; modelCalls: number; questionCount: number; passRate: number | null; citationCoverage: number | null}[]; limitations: string[] }
