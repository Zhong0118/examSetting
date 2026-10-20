import { ref } from 'vue'
import { api, setExpectedUser, setSessionBlocked, onSessionChanged, type User } from './api'
import { migrateGuestDrafts } from './drafts'
export const user = ref<User | null>(null)
export const notice = ref('')
export const authOpen = ref(false)
export const sessionFrozen = ref(false)
export const identityChanging = ref(false)
export const sessionIssue = ref('')
export const sessionSignalKey = 'examhub:session-change'
let timer: ReturnType<typeof setTimeout>
const guards = new Set<(reason: 'preserve' | 'confirm') => boolean>()
export function registerIdentityGuard(guard: (reason: 'preserve' | 'confirm') => boolean) {
  guards.add(guard)
  return () => guards.delete(guard)
}
export function notify(message: string) { notice.value = message; clearTimeout(timer); timer = setTimeout(() => notice.value = '', 4500) }
function adopt(next: User) { setExpectedUser(next.id); user.value=next; sessionFrozen.value=false; sessionIssue.value='' }
export async function initSession() { adopt((await api.session()).user) }
export function freezeSession() {
  setSessionBlocked(true)
  sessionFrozen.value=true
  authOpen.value=false
  for(const guard of guards) guard('preserve')
}
onSessionChanged(freezeSession)
export async function checkSession() {
  if(!user.value || identityChanging.value || sessionFrozen.value) return
  const previous=user.value
  try {
    const next=(await api.session()).user
    if(user.value===previous && (next.id!==previous.id || next.email!==previous.email)) freezeSession()
  } catch { /* Writes still carry the expected user when focus checks are offline. */ }
}
export function handleSessionSignal(event: StorageEvent) {
  if(event.key!==sessionSignalKey || !event.newValue || !user.value) return
  try { const signal=JSON.parse(event.newValue); if(signal.id!==user.value.id || signal.registered!==!!user.value.email) freezeSession() } catch { /* Ignore malformed storage events. */ }
}
function approveIdentityChange() {
  for(const guard of guards) if(!guard('confirm')) return false
  return true
}
export async function changeIdentity(operation: () => Promise<{user: User}>) {
  if(identityChanging.value || sessionFrozen.value || !approveIdentityChange()) return false
  const previous=user.value
  identityChanging.value=true
  try {
    // The client identity is deliberately unchanged until the old-identity write resolves.
    const next=(await operation()).user
    let migrationNote=''
    if(previous && !previous.email && next.email) {
      try { if(migrateGuestDrafts(previous,next)) migrationNote='目标账户已有草稿和生成任务优先保留，访客原始副本未删除' }
      catch { migrationNote='账户已切换，但浏览器未能迁移全部草稿；访客原稿未删除' }
    }
    adopt(next)
    try { localStorage.setItem(sessionSignalKey,JSON.stringify({id:next.id,registered:!!next.email,nonce:Date.now()})) } catch { /* Other tabs also check on focus and writes. */ }
    notify(migrationNote || '账户已切换')
    return true
  } finally { identityChanging.value=false }
}
export async function reconcileSession() {
  if(identityChanging.value || !approveIdentityChange()) return
  identityChanging.value=true
  try { adopt((await api.session()).user) }
  catch(e) { sessionIssue.value=message(e) }
  finally { identityChanging.value=false }
}
export function message(error: unknown) { return error instanceof Error ? error.message : '操作失败，请重试' }
export function date(value: string) { return new Date(value).toLocaleDateString('zh-CN', {month:'long',day:'numeric'}) }
export const visibilityLabels = {private:'仅自己',unlisted:'链接可见',public:'公开'}
