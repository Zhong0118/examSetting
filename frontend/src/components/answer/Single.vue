<script lang="ts" setup>
import {ref} from "vue";

const answer = ref()
const props = defineProps({
  options: Array,
})
</script>

<template>
  <div class="grid grid-cols-1 gap-2 mt-2">
    <div v-for="(result, index) in options" :key="index" class="flex flex-row gap-2">
      <input v-model="answer" :value="index" class="checkbox checkbox-secondary w-6 h-6 " name="single"
             type="radio"/>
      <span class="opposans">{{ result }}</span>
    </div>
  </div>
</template>

<style scoped>

</style>