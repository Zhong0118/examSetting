export interface User { id: string; name: string; email: string | null }
export type Visibility = 'private' | 'unlisted' | 'public'
export interface Question { id: string; type: 'single' | 'short'; prompt: string; options: string[]; answer?: string; explanation?: string; source: string; topic: string }
export type PracticeQuestion = Omit<Question, 'answer' | 'explanation'>
export interface SetSummary { id: string; title: string; description: string; topic: string; visibility: Visibility; version: number; questionCount: number; author: string; ownerId: string; isOwner: boolean; bookmarked: boolean; updatedAt: string; sourceSetId: string | null }
export interface SetDetail extends SetSummary { questions: Question[] }
export interface SetInput { title: string; description: string; topic: string; visibility: Visibility; questions: Question[]; version?: number }
export interface Result extends Question { userAnswer: string; correct: boolean | null; questionId: string }
export interface Attempt { id: string; setId: string; setTitle: string; version: number; createdAt: string; correct: number; total: number; results: Result[] }
export interface AIConfig { configured: boolean; baseUrl: string; model: string }
export interface Job { id: string; status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'; error: string | null; questions: Question[]; createdAt: string }
export class ApiError extends Error { constructor(message: string, public status: number, public code?: string) { super(message) } }
let expectedUser: string | null = null
let sessionBlocked = false
let identityGeneration = 0
let identityChanged: () => void = () => {}
export function setExpectedUser(value: string | null) { expectedUser = value; sessionBlocked = false; identityGeneration++ }
export function setSessionBlocked(value: boolean) { sessionBlocked = value; if(value) identityGeneration++ }
export function onSessionChanged(handler: () => void) { identityChanged = handler }
function identityError() { return new ApiError('账户已在其他页面切换；请确认当前账户后继续，原账户草稿已保留', 409, 'session_changed') }

export async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  if(sessionBlocked && path !== '/session') throw identityError()
  const generation = identityGeneration
  let response: Response
  try { response = await fetch(`/api${path}`, { method, credentials: 'same-origin', headers: { ...(method !== 'GET' ? { 'X-Requested-With': 'ExamHub', ...(expectedUser ? { 'X-Expected-User': expectedUser } : {}) } : {}), ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}) }, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) }) }
  catch { throw new ApiError('无法连接服务，请检查网络后重试', 0) }
  const data = await response.json().catch(() => null)
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
  startJob: (data: {source: string; title: string; topic: string; count: number}) => request<{job: Job}>('/ai/jobs', 'POST', data),
  job: (key: string) => request<{job: Job}>(`/ai/jobs/${id(key)}`),
  cancelJob: (key: string) => request<{job: Job}>(`/ai/jobs/${id(key)}`, 'DELETE'),
}
