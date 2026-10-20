<script setup lang="ts">
import { onBeforeUnmount, ref, watch, nextTick } from 'vue'
import Icon from './Icon.vue'
const props = defineProps<{open: boolean; title: string; dismissible?: boolean}>()
const emit = defineEmits<{close: []}>()
const panel = ref<HTMLElement>()
let previous: HTMLElement | null = null
function keydown(e: KeyboardEvent) {
  if (!props.open) return
  if (e.key === 'Escape' && props.dismissible!==false) emit('close')
  if (e.key === 'Tab') {
    const all = panel.value?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href]')
    if (!all?.length) return
    const first = all[0], last = all[all.length-1]
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
  }
}
watch(() => props.open, async open => { if (open) { previous = document.activeElement as HTMLElement; document.body.style.overflow = 'hidden'; document.addEventListener('keydown',keydown); await nextTick(); panel.value?.querySelector<HTMLElement>('input, button')?.focus() } else { document.body.style.overflow = ''; document.removeEventListener('keydown',keydown); previous?.focus() } })
onBeforeUnmount(() => { document.body.style.overflow = ''; document.removeEventListener('keydown',keydown) })
</script>
<template><Teleport to="body"><Transition name="modal"><div v-if="open" class="modal-backdrop" @click.self="dismissible!==false && emit('close')"><section ref="panel" class="modal-panel" role="dialog" aria-modal="true" :aria-label="title"><header class="section-head"><h2>{{title}}</h2><button v-if="dismissible!==false" class="icon-button" aria-label="关闭弹窗" @click="emit('close')"><Icon name="close"/></button></header><slot/></section></div></Transition></Teleport></template>
