<script setup lang="ts">
import { computed } from 'vue'
import Icon from './Icon.vue'
const props=defineProps<{page:number;total:number;pageSize:number;label?:string}>()
const emit=defineEmits<{change:[page:number]}>()
const pages=computed(()=>Math.ceil(props.total/props.pageSize))
</script>
<template>
  <Transition name="pagination">
    <nav v-if="pages>1" class="pagination" :aria-label="props.label||'题集分页'">
      <button type="button" class="button" :disabled="props.page<=1" @click="emit('change',props.page-1)"><Icon name="left"/>上一页</button>
      <span class="muted small" aria-live="polite">共 {{props.total}} 项 · 第 {{props.page}}/{{pages}} 页</span>
      <button type="button" class="button" :disabled="props.page>=pages" @click="emit('change',props.page+1)">下一页<Icon name="right"/></button>
    </nav>
  </Transition>
</template>
<style scoped>
.pagination{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:18px}
.pagination>span{text-align:center;font-variant-numeric:tabular-nums}
.pagination-enter-active,.pagination-leave-active{transition:opacity .18s ease,transform .18s ease}
.pagination-enter-from,.pagination-leave-to{opacity:0;transform:translateY(4px)}
@media(max-width:480px){.pagination{gap:8px}.pagination .button{padding:7px 9px}.pagination .icon{display:none}}
@media(prefers-reduced-motion:reduce){.pagination-enter-active,.pagination-leave-active{transition:none}}
</style>
