<script setup lang="ts">
import type { SetSummary } from '../lib/api'
import { date, visibilityLabels } from '../lib/state'
import Icon from './Icon.vue'
defineProps<{sets: SetSummary[]}>()
</script>
<template><div class="set-list"><RouterLink v-for="(set,index) in sets" :key="set.id" :to="`/sets/${set.id}`" class="set-row"><span class="set-symbol" :class="`symbol-${index%3}`"><Icon :name="index%3===0?'book':index%3===1?'library':'document'"/></span><div class="set-info"><div class="row"><span class="topic-label">{{set.topic||'综合学习'}}</span><span v-if="set.sourceSetId" class="small muted">改编题集</span></div><h3>{{set.title}}</h3><p>{{set.description || '打开题集，开始一次专注练习'}}</p><div class="set-meta"><span>{{set.questionCount}} 道题</span><span>{{set.author}}</span><span>{{date(set.updatedAt)}}更新</span></div></div><div class="set-trailing"><span class="visibility">{{visibilityLabels[set.visibility]}}</span><Icon name="right"/></div></RouterLink></div></template>
