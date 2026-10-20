export function draftKey(userId: string, setId: string, version: number) { return `examhub:answers:${userId}:${setId}:${version}` }
export function readDraft(key: string, ids: string[]): Record<string,string> {
  try { const data = JSON.parse(localStorage.getItem(key) || '{}'); return Object.fromEntries(Object.entries(data).filter(([id,value]) => ids.includes(id) && typeof value === 'string')) as Record<string,string> } catch { return {} }
}
export function writeDraft(key: string, answers: Record<string,string>) { localStorage.setItem(key, JSON.stringify(answers)) }

// Keep original guest copies. Existing account answers win; only missing answers merge.
export function migrateGuestDrafts(from: {id: string; email: string | null}, to: {id: string; email: string | null}) {
  if(from.email || !to.email || from.id === to.id) return 0
  let conflicts = 0
  const keys = Array.from({length:localStorage.length}, (_,i)=>localStorage.key(i)).filter((key): key is string => !!key)
  for(const kind of ['answers','editor','tutor:answer','tutor:command']) {
    const prefix = `examhub:${kind}:${from.id}:`
    for(const key of keys.filter(key=>key.startsWith(prefix))) {
      const target = `examhub:${kind}:${to.id}:${key.slice(prefix.length)}`
      const source = localStorage.getItem(key)!
      const existing = localStorage.getItem(target)
      if(!existing) { localStorage.setItem(target,source); continue }
      conflicts++
      if(kind==='answers') {
        try {
          const guest = JSON.parse(source), account = JSON.parse(existing)
          if(!guest || !account || typeof guest!=='object' || typeof account!=='object') continue
          const merged = {...guest,...account}
          for(const [id,answer] of Object.entries(guest)) if(typeof answer==='string' && !account[id]) merged[id]=answer
          localStorage.setItem(target,JSON.stringify(merged))
        } catch { /* Keep both originals if either draft is invalid. */ }
      }
    }
  }
  const guestJob=localStorage.getItem(`examhub:ai-job:${from.id}`)
  if(guestJob) {
    const target=`examhub:ai-job:${to.id}`
    if(localStorage.getItem(target)) conflicts++
    else localStorage.setItem(target,guestJob)
  }
  for(const kind of ['tutor:create','tutor:live-start']){
    const pending=localStorage.getItem(`examhub:${kind}:${from.id}`)
    if(pending){const target=`examhub:${kind}:${to.id}`;if(localStorage.getItem(target))conflicts++;else localStorage.setItem(target,pending)}
  }
  return conflicts
}
