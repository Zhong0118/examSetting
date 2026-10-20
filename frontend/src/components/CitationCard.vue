<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, ApiError, type Citation } from '../lib/api'
import { message } from '../lib/state'
import Icon from './Icon.vue'
const props=defineProps<{citation:Citation}>(),router=useRouter(),busy=ref(false),error=ref('')
async function open(){busy.value=true;error.value='';try{await api.document(props.citation.documentId);await router.push({path:`/documents/${props.citation.documentId}`,query:{page:props.citation.page,quote:props.citation.quote}})}catch(e){error.value=e instanceof ApiError&&e.status===404?'当前账户无权读取原教材，或原教材已删除。此处的引用快照仍然保留。':message(e)}finally{busy.value=false}}
</script>
<template><section class="citation-card"><div class="row"><Icon name="document"/><strong>{{citation.documentTitle}}</strong><span class="badge">物理页 {{citation.page}}</span></div><blockquote>{{citation.quote}}</blockquote><div class="citation-footer"><span>引用快照 · 原 PDF 仅所有者可读</span><button type="button" class="text-button" :disabled="busy" @click="open">{{busy?'正在确认权限…':'打开原页'}}<Icon name="right"/></button></div><p v-if="error" class="error" role="alert">{{error}}</p></section></template>
