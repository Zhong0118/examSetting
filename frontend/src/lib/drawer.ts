// A modal navigation drawer owns focus until it closes, including Escape from outside.
export function activateDrawer(panel: HTMLElement, background: HTMLElement, close: () => void) {
  const previous=document.activeElement as HTMLElement | null
  const overflow=document.body.style.overflow
  const wasInert=background.inert
  background.inert=true
  document.body.style.overflow='hidden'
  const focusable=()=>Array.from(panel.querySelectorAll<HTMLElement>('a[href],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')).filter(el=>!el.hidden)
  const focusFirst=()=>{(focusable()[0] || panel).focus()}
  function keydown(event: KeyboardEvent) {
    if(event.key==='Escape'){event.preventDefault();event.stopPropagation();close();return}
    if(event.key!=='Tab')return
    const list=focusable(),first=list[0],last=list[list.length-1]
    if(!first){event.preventDefault();panel.focus();return}
    if(!panel.contains(document.activeElement)){event.preventDefault();(event.shiftKey?last:first).focus();return}
    if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus()}
    else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus()}
  }
  function focusin(event: FocusEvent) { if(!panel.contains(event.target as Node))focusFirst() }
  document.addEventListener('keydown',keydown,true)
  document.addEventListener('focusin',focusin)
  focusFirst()
  return () => {
    document.removeEventListener('keydown',keydown,true)
    document.removeEventListener('focusin',focusin)
    background.inert=wasInert
    document.body.style.overflow=overflow
    if(previous?.isConnected)previous.focus()
  }
}
