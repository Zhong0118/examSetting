<script setup lang="ts">
import type { SetSummary } from '../lib/api'
import { date, visibilityLabels } from '../lib/state'
import Icon from './Icon.vue'
defineProps<{sets: SetSummary[]}>()
</script>
<template><TransitionGroup name="collection" tag="div" class="set-list"><RouterLink v-for="set in sets" :key="set.id" :to="`/sets/${set.id}`" class="set-row"><span class="set-symbol"><Icon name="book"/></span><div class="set-info"><h3>{{set.title}}</h3><p>{{set.description || '暂无题集说明'}}</p><div class="set-meta"><span>{{set.topic||'综合学习'}}</span><span>{{set.questionCount}} 道题</span><span>{{set.author}}</span><span>{{date(set.updatedAt)}}更新</span><span v-if="set.sourceSetId">改编题集</span></div></div><div class="set-trailing"><span class="visibility">{{visibilityLabels[set.visibility]}}</span><Icon name="right"/></div></RouterLink></TransitionGroup></template>
