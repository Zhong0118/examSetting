<script lang="ts" setup>
import {ref} from "vue";

const answer = ref([]);
const results = ref(['答案一', '答案2', '答案3', '答案4', '答案5', '答案6', '答案7'])
</script>

<template>
  <div class="grid grid-cols-1 gap-2 mt-2">
    <div v-for="(result, index) in results" :key="index" class="flex flex-row gap-2">
      <input v-model="answer" :value="index" class="checkbox checkbox-secondary w-6 h-6 "
             name="multiple"
             type="checkbox"/>
      <span class="opposans">{{ result }}</span>
    </div>
  </div>
</template>

<style scoped>

</style>